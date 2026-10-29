// SPDX-License-Identifier: GPL-2.0-only
/*
 * LAB SIMULATION ONLY: emulated UGREEN DXP4800 Pro front-panel LED MCU.
 *
 * Registers an SMBus adapter whose name matches the Intel I801 controller used
 * by the NAS and answers at 0x3a with the legacy MCU protocol implemented by
 * led-ugreen. The production driver, monitor and installer therefore run
 * unchanged in the test VM. The module refuses to load without a hypervisor.
 *
 * /proc/ugreen-mcu-sim/state   current state of each LED
 * /proc/ugreen-mcu-sim/events  recent accepted commands with timestamps
 */
#include <linux/i2c.h>
#include <linux/kernel.h>
#include <linux/ktime.h>
#include <linux/module.h>
#include <linux/mutex.h>
#include <linux/platform_device.h>
#include <linux/proc_fs.h>
#include <linux/seq_file.h>
#include <asm/cpufeature.h>

#define SIM_ADDR 0x3a
#define SIM_CHIP_ID 0xc5b2
#define SIM_REG_CHIP_ID 0x5a
#define SIM_REG_STATUS 0x80
#define SIM_REG_STATE 0x81
#define SIM_MAX_LEDS 10
#define SIM_EVENTS 1024

enum { LED_OFF, LED_ON, LED_BLINK, LED_BREATH };

struct sim_led {
	u8 status, brightness, r, g, b;
	u16 t_on, t_cycle;
};

struct sim_event {
	u64 seq, ns;
	u8 led, command, p[4];
};

static unsigned int num_leds = 6;
module_param(num_leds, uint, 0444);
MODULE_PARM_DESC(num_leds, "LEDs answered by the MCU: power, netdev and drive bays (default 6)");

static const char *const led_names[SIM_MAX_LEDS] = {
	"power", "netdev", "disk1", "disk2", "disk3", "disk4", "disk5", "disk6", "disk7", "disk8",
};
static const char *const status_names[] = { "off", "on", "blink", "breath" };

static DEFINE_MUTEX(sim_lock);
static struct sim_led leds[SIM_MAX_LEDS];
static struct sim_event events[SIM_EVENTS];
static u64 event_seq;
static u8 last_status;
static u64 rejected;
static struct platform_device *sim_pdev;
static struct i2c_adapter sim_adapter;
static struct proc_dir_entry *sim_proc;

static void sim_reset(void)
{
	unsigned int i;

	/* At power-on the MCU lights the power LED; the others stay dark. */
	for (i = 0; i < SIM_MAX_LEDS; ++i)
		leds[i] = (struct sim_led){ .status = i ? LED_OFF : LED_ON, .brightness = 255,
					    .r = 255, .g = 255, .b = 255 };
}

/* Apply one legacy frame: led_id, a0 01 00 00, command, p1..p4, checksum (big endian). */
static bool sim_apply(u8 reg, const u8 *buf, u8 len)
{
	struct sim_led *led;
	struct sim_event *event;
	u16 sum;
	int i;

	if (reg >= num_leds || len != 12 || buf[0] != reg ||
	    buf[1] != 0xa0 || buf[2] != 0x01 || buf[3] != 0x00 || buf[4] != 0x00)
		return false;
	sum = 0xa1;
	for (i = 5; i < 10; ++i)
		sum += buf[i];
	if (sum != (((u16)buf[10] << 8) | buf[11]))
		return false;
	led = &leds[reg];
	switch (buf[5]) {
	case 0x01:
		led->brightness = buf[6];
		break;
	case 0x02:
		led->r = buf[6];
		led->g = buf[7];
		led->b = buf[8];
		break;
	case 0x03:
		led->status = buf[6] ? LED_ON : LED_OFF;
		break;
	case 0x04:
	case 0x05:
		led->t_cycle = ((u16)buf[6] << 8) | buf[7];
		led->t_on = ((u16)buf[8] << 8) | buf[9];
		led->status = buf[5] == 0x04 ? LED_BLINK : LED_BREATH;
		break;
	default:
		return false;
	}
	event = &events[event_seq % SIM_EVENTS];
	*event = (struct sim_event){ .seq = ++event_seq, .ns = ktime_get_ns(), .led = reg, .command = buf[5] };
	memcpy(event->p, buf + 6, 4);
	return true;
}

/* State frame read at 0x81 + id: status, brightness, rgb, t_cycle, t_on, sum (big endian). */
static void sim_state_frame(u8 id, u8 *out, u8 len)
{
	u8 frame[11] = { 0 };
	u16 sum = 0;
	int i;

	if (id < num_leds) {
		const struct sim_led *led = &leds[id];

		frame[0] = led->status;
		frame[1] = led->brightness;
		frame[2] = led->r;
		frame[3] = led->g;
		frame[4] = led->b;
		frame[5] = led->t_cycle >> 8;
		frame[6] = led->t_cycle & 0xff;
		frame[7] = led->t_on >> 8;
		frame[8] = led->t_on & 0xff;
		for (i = 0; i < 9; ++i)
			sum += frame[i];
		frame[9] = sum >> 8;
		frame[10] = sum & 0xff;
	}
	memcpy(out, frame, min_t(u8, len, sizeof(frame)));
	if (len > sizeof(frame))
		memset(out + sizeof(frame), 0, len - sizeof(frame));
}

static int sim_smbus_xfer(struct i2c_adapter *adap, u16 addr, unsigned short flags,
			  char read_write, u8 command, int size, union i2c_smbus_data *data)
{
	int rc = 0;

	if (addr != SIM_ADDR)
		return -ENXIO;
	mutex_lock(&sim_lock);
	switch (size) {
	case I2C_SMBUS_QUICK:
		break;
	case I2C_SMBUS_BYTE:
		if (read_write == I2C_SMBUS_READ)
			data->byte = 0;
		break;
	case I2C_SMBUS_BYTE_DATA:
		if (read_write == I2C_SMBUS_READ)
			data->byte = command == SIM_REG_STATUS ? last_status : 0;
		break;
	case I2C_SMBUS_WORD_DATA:
		if (read_write == I2C_SMBUS_READ)
			data->word = command == SIM_REG_CHIP_ID ? SIM_CHIP_ID : 0;
		break;
	case I2C_SMBUS_I2C_BLOCK_DATA:
		if (data->block[0] == 0 || data->block[0] > I2C_SMBUS_BLOCK_MAX) {
			rc = -EINVAL;
		} else if (read_write == I2C_SMBUS_READ) {
			if (command >= SIM_REG_STATE)
				sim_state_frame(command - SIM_REG_STATE, data->block + 1, data->block[0]);
			else
				memset(data->block + 1, 0, data->block[0]);
		} else {
			last_status = sim_apply(command, data->block + 1, data->block[0]);
			if (!last_status)
				++rejected;
		}
		break;
	case I2C_SMBUS_BLOCK_DATA:
		/* The DXP4800 Pro MCU ACKs other framings but does not execute them. */
		if (read_write == I2C_SMBUS_WRITE) {
			last_status = 0;
			++rejected;
		} else {
			data->block[0] = 0;
		}
		break;
	default:
		rc = -EOPNOTSUPP;
	}
	mutex_unlock(&sim_lock);
	return rc;
}

static u32 sim_functionality(struct i2c_adapter *adap)
{
	return I2C_FUNC_SMBUS_QUICK | I2C_FUNC_SMBUS_BYTE | I2C_FUNC_SMBUS_BYTE_DATA |
	       I2C_FUNC_SMBUS_WORD_DATA | I2C_FUNC_SMBUS_BLOCK_DATA | I2C_FUNC_SMBUS_I2C_BLOCK;
}

static const struct i2c_algorithm sim_algorithm = {
	.smbus_xfer = sim_smbus_xfer,
	.functionality = sim_functionality,
};

static int sim_state_show(struct seq_file *m, void *v)
{
	unsigned int i;

	mutex_lock(&sim_lock);
	seq_printf(m, "now %llu\nseq %llu\nrejected %llu\n", ktime_get_ns(), event_seq, rejected);
	for (i = 0; i < num_leds; ++i)
		seq_printf(m, "led %u %s %s %u %u %u %u %u %u\n", i, led_names[i],
			   status_names[leds[i].status], leds[i].brightness, leds[i].r, leds[i].g,
			   leds[i].b, leds[i].t_on, leds[i].t_cycle);
	mutex_unlock(&sim_lock);
	return 0;
}

static int sim_events_show(struct seq_file *m, void *v)
{
	u64 seq, first;

	mutex_lock(&sim_lock);
	seq_printf(m, "now %llu\n", ktime_get_ns());
	first = event_seq > SIM_EVENTS ? event_seq - SIM_EVENTS + 1 : 1;
	for (seq = first; seq <= event_seq; ++seq) {
		const struct sim_event *e = &events[(seq - 1) % SIM_EVENTS];

		seq_printf(m, "%llu %llu %u %02x %u %u %u %u\n", e->seq, e->ns, e->led, e->command,
			   e->p[0], e->p[1], e->p[2], e->p[3]);
	}
	mutex_unlock(&sim_lock);
	return 0;
}

static int __init sim_init(void)
{
	int rc;

	if (!boot_cpu_has(X86_FEATURE_HYPERVISOR)) {
		pr_err("ugreen-mcu-sim: LAB ONLY, refusing to load outside a virtual machine\n");
		return -EPERM;
	}
	if (num_leds < 2 || num_leds > SIM_MAX_LEDS)
		return -EINVAL;
	sim_reset();
	sim_pdev = platform_device_register_simple("ugreen-mcu-sim", -1, NULL, 0);
	if (IS_ERR(sim_pdev))
		return PTR_ERR(sim_pdev);
	sim_adapter = (struct i2c_adapter){
		.owner = THIS_MODULE,
		.algo = &sim_algorithm,
		.dev.parent = &sim_pdev->dev,
	};
	/* The plugin selects its controller by this adapter name. */
	strscpy(sim_adapter.name, "SMBus I801 adapter (UGREEN MCU simulator)", sizeof(sim_adapter.name));
	rc = i2c_add_adapter(&sim_adapter);
	if (rc)
		goto unregister;
	sim_proc = proc_mkdir("ugreen-mcu-sim", NULL);
	if (!sim_proc || !proc_create_single("state", 0444, sim_proc, sim_state_show) ||
	    !proc_create_single("events", 0444, sim_proc, sim_events_show)) {
		rc = -ENOMEM;
		goto remove;
	}
	pr_info("ugreen-mcu-sim: LAB SIMULATION, MCU at 0x%02x on %s\n", SIM_ADDR, dev_name(&sim_adapter.dev));
	return 0;
remove:
	proc_remove(sim_proc);
	i2c_del_adapter(&sim_adapter);
unregister:
	platform_device_unregister(sim_pdev);
	return rc;
}

static void __exit sim_exit(void)
{
	proc_remove(sim_proc);
	i2c_del_adapter(&sim_adapter);
	platform_device_unregister(sim_pdev);
}

module_init(sim_init);
module_exit(sim_exit);
MODULE_DESCRIPTION("LAB ONLY: emulated UGREEN DXP4800 Pro LED MCU on a simulated SMBus");
MODULE_LICENSE("GPL");
