import fs from 'node:fs';

const file = 'src/lib/supabase.ts';
const source = fs.readFileSync(file, 'utf8');

const oldBlock = `    const { data: result, error } = await supabase.rpc('custom_create_order', {\n      p_student_id: orderData.student.id,\n      p_service_id: orderData.service.id,`;

const newBlock = `    // The UI keeps legacy service IDs (srv-*) for compatibility, while the\n    // central services table uses canonical IDs. Normalize before the RPC.\n    const serviceIdAliases: Record<string, string> = {\n      'srv-ppt': 'ppt',\n      'srv-excel': 'excel',\n      'srv-word': 'word',\n      'srv-pdf': 'pdf',\n      'srv-video': 'edit-video',\n      'srv-desain': 'desain',\n      'srv-transkrip': 'transkripsi',\n      'srv-data': 'input-data',\n      'srv-aplikasi': 'aplikasi',\n      'srv-website': 'website',\n      'srv-custom': 'custom',\n    };\n    const remoteServiceId = serviceIdAliases[orderData.service.id] || orderData.service.id;\n\n    const { data: result, error } = await supabase.rpc('custom_create_order', {\n      p_student_id: orderData.student.id,\n      p_service_id: remoteServiceId,`;

if (!source.includes(oldBlock)) {
  throw new Error('Expected createRemoteOrder block was not found.');
}
if (source.includes('const serviceIdAliases: Record<string, string>')) {
  console.log('Service ID alias mapping already present.');
  process.exit(0);
}

fs.writeFileSync(file, source.replace(oldBlock, newBlock));
console.log('Patched service ID aliases in src/lib/supabase.ts');
