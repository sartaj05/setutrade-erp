export const demoCrm = {
  summary:{pipelineValue:1840000,wonValue:680000,conversion:18.4},
  stages:[{status:'New',count:48,value:620000},{status:'Qualified',count:21,value:540000},{status:'Quoted',count:14,value:410000},{status:'Negotiation',count:7,value:270000},{status:'Won',count:5,value:680000}],
  leads:[{id:1,leadNo:'LEAD-2609-041',name:'Sanjay Verma',business:'Verma Electrical House',status:'Negotiation',source:'Referral',territory:'West Delhi',value:185000,close:'2026-09-28',owner:'Rohit Bansal'},{id:2,leadNo:'LEAD-2609-042',name:'Pooja Jain',business:'Jain Buildmart',status:'Quoted',source:'Website',territory:'Noida',value:242000,close:'2026-10-03',owner:'Rohit Bansal'}],
  activities:[{id:1,lead:'Verma Electrical House',type:'Meeting',note:'Commercial terms reviewed; revised quotation requested.',next:'2026-09-23T11:00:00+05:30',completed:false}]
};

export const demoSchemes={summary:{active:4,accrued:128400,claims:3},schemes:[{id:1,name:'Q3 Electrical Growth Rebate',supplier:'Polycab India',type:'Rebate',start:'2026-07-01',end:'2026-09-30',target:5000000,rebate:1.5,active:true},{id:2,name:'MCB Volume Slab',supplier:'Anchor by Panasonic',type:'Slab',start:'2026-09-01',end:'2026-09-30',target:800000,rebate:2.25,active:true}],claims:[{id:1,claimNo:'CLM-2609-014',scheme:'Q3 Electrical Growth Rebate',supplier:'Polycab India',eligible:4280000,amount:64200,status:'Accrued'},{id:2,claimNo:'CLM-2609-012',scheme:'MCB Volume Slab',supplier:'Anchor by Panasonic',eligible:2850000,amount:64125,status:'Submitted'}]};
