from pathlib import Path
import re

ROOT = Path('.')
store = ROOT / 'src/lib/supabase.ts'
admin = ROOT / 'src/components/AdminPaymentSettings.tsx'
qris = ROOT / 'src/components/QRISPaymentModal.tsx'
app = ROOT / 'src/App.tsx'
landing = ROOT / 'src/components/LandingPage.tsx'
seo = ROOT / 'src/components/ServiceSeoPage.tsx'

# Canonical payment/contact values.
REPLACEMENTS = {
    "08136732365": "628136732365",
    "887012345678": "081224405119",
    "BERESIN JASA": "Hesti Kurnia",
}

s = store.read_text()
s = s.replace("whatsapp_number: '08136732365'", "whatsapp_number: '628136732365'")
s = s.replace("bank_name: 'BCA'", "bank_name: 'DANA'")
s = s.replace("bank_account_number: '887012345678'", "bank_account_number: '081224405119'")
s = s.replace("bank_account_holder: 'BERESIN JASA'", "bank_account_holder: 'Hesti Kurnia'")

# Replace the local-only payment getters in the current source layout.
pattern = re.compile(r"  static getPaymentConfig\(\): AdminPaymentConfig \{.*?\n  static getWhatsAppLink", re.S)
replacement = '''  static getPaymentConfig(): AdminPaymentConfig {
    const stored = getStored<AdminPaymentConfig>(STORAGE_KEYS.PAYMENT_CONFIG, DEFAULT_PAYMENT_CONFIG);
    if (stored.bank_account_number === '887012345678' || stored.whatsapp_number === '08136732365') {
      return { ...DEFAULT_PAYMENT_CONFIG, ...stored,
        whatsapp_number: DEFAULT_PAYMENT_CONFIG.whatsapp_number,
        bank_name: DEFAULT_PAYMENT_CONFIG.bank_name,
        bank_account_number: DEFAULT_PAYMENT_CONFIG.bank_account_number,
        bank_account_holder: DEFAULT_PAYMENT_CONFIG.bank_account_holder,
      };
    }
    return stored;
  }

  static async loadPaymentConfig(): Promise<AdminPaymentConfig> {
    const supabase = getSupabase();
    if (!supabase) return this.getPaymentConfig();
    const { data, error } = await supabase.rpc('custom_get_payment_config');
    const remoteConfig = data?.config ?? data?.data?.config ?? data?.data;
    if (error || !data?.success || !remoteConfig) return this.getPaymentConfig();
    const config = { ...DEFAULT_PAYMENT_CONFIG, ...(remoteConfig as Partial<AdminPaymentConfig>) };
    setStored(STORAGE_KEYS.PAYMENT_CONFIG, config);
    return config;
  }

  static async savePaymentConfig(config: AdminPaymentConfig, adminUserId?: string): Promise<{ success: boolean; message: string; config?: AdminPaymentConfig }> {
    setStored(STORAGE_KEYS.PAYMENT_CONFIG, config);
    const supabase = getSupabase();
    if (!supabase || !adminUserId) return { success: true, message: 'Tersimpan di perangkat.', config };
    const { data, error } = await supabase.rpc('custom_save_payment_config', {
      p_admin_user_id: adminUserId,
      p_config: config,
    });
    if (error || !data?.success) return { success: false, message: error?.message || data?.message || 'Gagal menyimpan pengaturan ke server.' };
    const saved = (data.config || config) as AdminPaymentConfig;
    setStored(STORAGE_KEYS.PAYMENT_CONFIG, saved);
    return { success: true, message: data.message || 'Berhasil disimpan.', config: saved };
  }

  static getWhatsAppLink'''
if pattern.search(s):
    s = pattern.sub(replacement, s, count=1)
else:
    # If already patched, keep the existing implementation.
    pass
store.write_text(s)

s = admin.read_text()
s = s.replace("import React, { useState } from 'react';", "import React, { useEffect, useState } from 'react';", 1)
if "useAuth" not in s:
    s = s.replace("import { BeresinDataStore } from '../lib/supabase';", "import { BeresinDataStore } from '../lib/supabase';\nimport { useAuth } from '../context/AuthContext';", 1)
s = s.replace("whatsapp_number: '6281234567890'", "whatsapp_number: '628136732365'")
s = s.replace("bank_name: 'BCA (Bank Central Asia)'", "bank_name: 'DANA'")
s = s.replace("bank_account_number: '887012345678'", "bank_account_number: '081224405119'")
s = s.replace("bank_account_holder: 'BERESIN OFFICIAL'", "bank_account_holder: 'Hesti Kurnia'")

# Make admin save persist to Supabase instead of only localStorage.
s = s.replace("  const [config, setConfig] = useState<AdminPaymentConfig>(() => BeresinDataStore.getPaymentConfig());", "  const { currentUser } = useAuth();\n  const [config, setConfig] = useState<AdminPaymentConfig>(() => BeresinDataStore.getPaymentConfig());\n  const [isSaving, setIsSaving] = useState(false);", 1)
old_handler = """  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    BeresinDataStore.savePaymentConfig(config);
    setSuccessMessage('Pengaturan Kartu Bank & Kontak WhatsApp berhasil disimpan!');
    onSaved?.();
    setTimeout(() => {
      setSuccessMessage('');
    }, 3000);
  };"""
new_handler = """  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentUser?.id || isSaving) return;
    setIsSaving(true);
    const result = await BeresinDataStore.savePaymentConfig(config, currentUser.id);
    setIsSaving(false);
    if (!result.success) { window.alert(result.message); return; }
    if (result.config) setConfig(result.config);
    setSuccessMessage('Pengaturan Kartu Bank & Kontak WhatsApp berhasil disimpan di server!');
    onSaved?.();
    setTimeout(() => setSuccessMessage(''), 3000);
  };"""
s = s.replace(old_handler, new_handler, 1)
if "BeresinDataStore.loadPaymentConfig()" not in s:
    marker = "  const handleChange = (field: keyof AdminPaymentConfig, value: string) => {"
    if marker in s:
        effect = """  useEffect(() => {
    let active = true;
    void BeresinDataStore.loadPaymentConfig().then(remote => { if (active) setConfig(remote); });
    return () => { active = false; };
  }, []);

"""
        s = s.replace(marker, effect + marker, 1)
admin.write_text(s)

# QRIS must refresh from the central server whenever it opens.
s = qris.read_text()
if "BeresinDataStore.loadPaymentConfig()" not in s:
    s = s.replace("setPaymentConfig(BeresinDataStore.getPaymentConfig());", "void BeresinDataStore.loadPaymentConfig().then(remote => setPaymentConfig(remote));", 1)
qris.write_text(s)

# Ensure the main app hydrates central payment settings on startup/login.
s = app.read_text()
if "BeresinDataStore.loadPaymentConfig()" not in s:
    marker = "  useEffect(() => {\n    refreshData();\n  }, [currentUser, role]);"
    if marker in s:
        s = s.replace(marker, marker + "\n\n  useEffect(() => {\n    void BeresinDataStore.loadPaymentConfig();\n  }, [currentUser?.id]);", 1)
app.write_text(s)

# Replace hardcoded WhatsApp contact usage in public-facing pages.
s = landing.read_text()
if "BeresinDataStore" not in s:
    marker = "import { ServiceItem } from '../types';"
    if marker in s:
        s = s.replace(marker, marker + "\nimport { BeresinDataStore } from '../lib/supabase';", 1)
s = s.replace("const WHATSAPP_NUMBER = '08136732365';", "const WHATSAPP_NUMBER = BeresinDataStore.getPaymentConfig().whatsapp_number;")
s = s.replace("https://wa.me/628136732365?text=", "https://wa.me/628136732365?text=")
landing.write_text(s)

s = seo.read_text()
if "BeresinDataStore" not in s:
    marker = "import React, { useEffect, useState } from 'react';"
    if marker in s:
        s = s.replace(marker, marker + "\nimport { BeresinDataStore } from '../lib/supabase';", 1)
s = s.replace("const WHATSAPP_NUMBER = '08136732365';", "const WHATSAPP_NUMBER = BeresinDataStore.getPaymentConfig().whatsapp_number;")
s = s.replace("https://wa.me/628136732365?text=${whatsappMessage}", "${BeresinDataStore.getWhatsAppLink(whatsappMessage)}")
seo.write_text(s)

# Final source-level guard: no retired account/contact should survive into the build.
for path in ROOT.glob('src/**/*.ts*'):
    text = path.read_text()
    for old, new in REPLACEMENTS.items():
        text = text.replace(old, new)
    path.write_text(text)

print('OK: payment config defaults and central Supabase sync patched')
