const assert = require('node:assert/strict'), fs = require('node:fs'), vm = require('node:vm');
const inputs = ['#ffffff','#ffa500'].map(value=>({value, events:{}, parentElement:{notice:{hidden:true},querySelector(){return this.notice;}},addEventListener(event,fn){this.events[event]=fn;}}));
const panel={dataset:{},querySelectorAll:selector=>selector==='input[type="color"]'?inputs:[],addEventListener(){}};
vm.runInNewContext(fs.readFileSync('src/web/settings.js','utf8'),{document:{querySelectorAll:()=>[panel],querySelector:()=>null}});
for(const input of inputs){
 const initial=input.value;
 for(const value of ['#000000','transparent','#ff000000','']){
  input.value=value;input.events.input();assert.equal(input.value,initial);assert.equal(input.parentElement.notice.hidden,false);
 }
 input.value='#000001';input.events.input();assert.equal(input.parentElement.notice.hidden,true);
 input.value='#000000';input.events.change();assert.equal(input.value,'#000001');
 input.value='#12ab34';input.events.change();input.value='#000000';input.events.input();assert.equal(input.value,'#12ab34');
}
console.log('Colour picker rejects black/alpha/empty values, restores the latest valid colour and accepts dark opaque RGB.');
