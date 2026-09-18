from pathlib import Path

ROOT = Path('.')
store = ROOT / 'src/lib/supabase.ts'
admin = ROOT / 'src/components/AdminPaymentSettings.tsx'
qris = ROOT / 'src/components/QRISPaymentModal.tsx'
app = ROOT / 'src/App.tsx'
landing = ROOT / 'src/components/LandingPage.tsx'
seo = ROOT / 'src/components/ServiceSeoPage.tsx'
promo = ROOT / 'src/components/PromoBanner.tsx'
voucher = ROOT / 'src/components/VoucherTab.tsx'

s = store.read_text()
old = """  static getPaymentConfig(): AdminPaymentConfig {
    return getStored<AdminPaymentConfig>(STORAGE_KEYS.PAYMENT_CONFIG, DEFAULT_PAYMENT_CONFIG);
  }

  static savePaymentConfig(config: AdminPaymentConfig): void {
    setStored(STORAGE_KEYS.PAYMENT_CONFIG, config);
  }
"""
new = """  static getPaymentConfig(): AdminPaymentConfig {
    return getStored<AdminPaymentConfig>(STORAGE_KEYS.PAYMENT_CONFIG, DEFAULT_PAYMENT_CONFIG);
  }

  static async loadPaymentConfig(): Promise<AdminPaymentConfig> {
    const supabase = getSupabase();
    if (!supabase) return this.getPaymentConfig();
    const { data, error } = await supabase.rpc('custom_get_payment_config');
    const payload = data?.config ?? data;
    const remoteConfig = payload?.config ?? payload;
    if (error || !data?.success && !payload?.success || !remoteConfig) return this.getPaymentConfig();
    const config = { ...DEFAULT_PAYMENT_CONFIG, ...(remoteConfig as Partial<AdminPaymentConfig>) };
    setStored(STORAGE_KEYS.PAYMENT_CONFIG, config);
    return config;
  }

  static async savePaymentConfig(config: AdminPaymentConfig, adminUserId?: string): Promise<{ success: boolean; message: string; config?: AdminPaymentConfig }> {
    const supabase = getSupabase();
    if (!supabase || !adminUserId) {
      setStored(STORAGE_KEYS.PAYMENT_CONFIG, config);
      return { success: true, message: 'Tersimpan di perangkat.', config };
    }
    const { data, error } = await supabase.rpc('custom_save_payment_config', {
      p_admin_user_id: adminUserId,
      p_config: config,
    });
    const payload = data?.config ?? data;
    if (error || !data?.success && !payload?.success) return { success: false, message: error?.message || data?.message || payload?.message || 'Gagal menyimpan pengaturan ke server.' };
    setStored(STORAGE_KEYS.PAYMENT_CONFIG, config);
    return { success: true, message: data.message || payload?.message || 'Berhasil disimpan.', config };
  }
"""
if old not in s: raise SystemExit('payment methods marker missing')
s = s.replace(old, new, 1)
store.write_text(s)

s = admin.read_text()
s = s.replace("import React, { useState } from 'react';", "import React, { useEffect, useState } from 'react';")
s = s.replace("import { BeresinDataStore } from '../lib/supabase';", "import { BeresinDataStore } from '../lib/supabase';\nimport { useAuth } from '../context/AuthContext';")
s = s.replace("  const [config, setConfig] = useState<AdminPaymentConfig>(() => BeresinDataStore.getPaymentConfig());", "  const { currentUser } = useAuth();\n  const [config, setConfig] = useState<AdminPaymentConfig>(() => BeresinDataStore.getPaymentConfig());\n  const [isSaving, setIsSaving] = useState(false);\n\n  useEffect(() => {\n    let active = true;\n    void BeresinDataStore.loadPaymentConfig().then(remote => { if (active) setConfig(remote); });\n    return () => { active = false; };\n  }, []);")
old = """  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    BeresinDataStore.savePaymentConfig(config);
    setSuccessMessage('Pengaturan Kartu Bank & Kontak WhatsApp berhasil disimpan!');
    onSaved?.();
    setTimeout(() => {
      setSuccessMessage('');
    }, 3000);
  };"""
new = """  const handleSave = async (e: React.FormEvent) => {
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
if old not in s: raise SystemExit('admin save handler missing')
s = s.replace(old, new, 1)
s = s.replace("      BeresinDataStore.savePaymentConfig(defaultConfig);\n      setConfig(defaultConfig);", "      if (!currentUser?.id) return;\n      void BeresinDataStore.savePaymentConfig(defaultConfig, currentUser.id).then(result => {\n        if (!result.success) window.alert(result.message);\n        else setConfig(result.config || defaultConfig);\n      });")
admin.write_text(s)

s = qris.read_text()
old = """  useEffect(() => {
    if (isOpen) {
      setPaymentConfig(BeresinDataStore.getPaymentConfig());
    }
  }, [isOpen]);"""
new = """  useEffect(() => {
    if (!isOpen) return;
    let active = true;
    void BeresinDataStore.loadPaymentConfig().then(remote => { if (active) setPaymentConfig(remote); });
    return () => { active = false; };
  }, [isOpen]);"""
if old not in s: raise SystemExit('QRIS config effect missing')
s = s.replace(old, new, 1)
qris.write_text(s)

s = app.read_text()
if 'setPaymentConfigVersion' not in s:
    marker = "  const [proofPreviewName, setProofPreviewName] = useState<string>('');"
    if marker not in s: raise SystemExit('App payment state marker missing')
    s = s.replace(marker, marker + "\n  const [, setPaymentConfigVersion] = useState(0);", 1)
marker = """  useEffect(() => {
    refreshData();
  }, [currentUser, role]);"""
if marker not in s: raise SystemExit('App refresh marker missing')
if 'loadPaymentConfig' not in s:
    s = s.replace(marker, marker + "\n\n  useEffect(() => {\n    void BeresinDataStore.loadPaymentConfig().then(() => setPaymentConfigVersion(v => v + 1));\n  }, [currentUser?.id]);", 1)
app.write_text(s)

s = landing.read_text()
if "../lib/supabase" not in s:
    marker = "import { ServiceItem } from '../types';"
    if marker not in s: raise SystemExit('Landing import marker missing')
    s = s.replace(marker, marker + "\nimport { BeresinDataStore } from '../lib/supabase';", 1)
s = s.replace("  const WHATSAPP_NUMBER = '08136732365';\n  const WHATSAPP_LINK = 'https://wa.me/628136732365?text=Halo%20Admin%20BERESIN,%20saya%20mau%20konsultasi%20jasa%20tugas%20dan%20voucher';", "  const paymentConfig = BeresinDataStore.getPaymentConfig();\n  const WHATSAPP_NUMBER = paymentConfig.whatsapp_number;\n  const WHATSAPP_LINK = BeresinDataStore.getWhatsAppLink('Halo Admin BERESIN, saya mau konsultasi jasa tugas dan voucher');")
landing.write_text(s)

s = seo.read_text()
if "../lib/supabase" not in s:
    marker = "import React, { useEffect, useState } from 'react';"
    if marker not in s: raise SystemExit('SEO import marker missing')
    s = s.replace(marker, marker + "\nimport { BeresinDataStore } from '../lib/supabase';", 1)
s = s.replace("  const WHATSAPP_NUMBER = '08136732365';", "  const WHATSAPP_NUMBER = BeresinDataStore.getPaymentConfig().whatsapp_number;")
s = s.replace("  const whatsappUrl = `https://wa.me/628136732365?text=${whatsappMessage}`;", "  const whatsappUrl = BeresinDataStore.getWhatsAppLink(whatsappMessage);")
seo.write_text(s)

for path in (promo, voucher):
    s = path.read_text()
    if "../lib/supabase" not in s:
        first_import = next((line for line in s.splitlines() if line.startswith('import ')), None)
        if first_import:
            s = s.replace(first_import, first_import + "\nimport { BeresinDataStore } from '../lib/supabase';", 1)
    s = s.replace('href="https://wa.me/6281234567890?text=Halo%20Admin%20BERESIN,%20saya%20mau%20beli%20kode%20voucher%20promo%20Rp10.000%20(dapat%20Rp30.000)"', 'href={BeresinDataStore.getWhatsAppLink(\'Halo Admin BERESIN, saya mau beli kode voucher promo Rp10.000 (dapat Rp30.000)\')}')
    path.write_text(s)
