from pathlib import Path

ROOT = Path('.')
store = ROOT / 'src/lib/supabase.ts'
admin = ROOT / 'src/components/AdminPaymentSettings.tsx'
qris = ROOT / 'src/components/QRISPaymentModal.tsx'
app = ROOT / 'src/App.tsx'
landing = ROOT / 'src/components/LandingPage.tsx'
seo = ROOT / 'src/components/ServiceSeoPage.tsx'

# Current payment defaults. Also neutralize the retired values if they remain in localStorage/source.
s = store.read_text()
for old, new in [
    ("whatsapp_number: '08136732365'", "whatsapp_number: '628136732365'"),
    ("bank_name: 'BCA'", "bank_name: 'DANA'"),
    ("bank_account_number: '887012345678'", "bank_account_number: '081224405119'"),
    ("bank_account_holder: 'BERESIN JASA'", "bank_account_holder: 'Hesti Kurnia'"),
]:
    s = s.replace(old, new)
old = '''  static getPaymentConfig(): AdminPaymentConfig {\n    return getStored<AdminPaymentConfig>(STORAGE_KEYS.PAYMENT_CONFIG, DEFAULT_PAYMENT_CONFIG);\n  }\n\n  static savePaymentConfig(config: AdminPaymentConfig): void {\n    setStored(STORAGE_KEYS.PAYMENT_CONFIG, config);\n  }\n'''
if old not in s:
    raise SystemExit('payment methods marker missing')
new = '''  static getPaymentConfig(): AdminPaymentConfig {\n    const stored = getStored<AdminPaymentConfig>(STORAGE_KEYS.PAYMENT_CONFIG, DEFAULT_PAYMENT_CONFIG);\n    if (stored.bank_account_number === '887012345678' || stored.whatsapp_number === '08136732365') {\n      return { ...DEFAULT_PAYMENT_CONFIG, ...stored, whatsapp_number: DEFAULT_PAYMENT_CONFIG.whatsapp_number, bank_name: DEFAULT_PAYMENT_CONFIG.bank_name, bank_account_number: DEFAULT_PAYMENT_CONFIG.bank_account_number, bank_account_holder: DEFAULT_PAYMENT_CONFIG.bank_account_holder };\n    }\n    return stored;\n  }\n\n  static async loadPaymentConfig(): Promise<AdminPaymentConfig> {\n    const supabase = getSupabase();\n    if (!supabase) return this.getPaymentConfig();\n    const { data, error } = await supabase.rpc('custom_get_payment_config');\n    const payload = data?.config ?? data;\n    const remoteConfig = payload?.config ?? payload;\n    if (error || (!data?.success && !payload?.success) || !remoteConfig) return this.getPaymentConfig();\n    const config = { ...DEFAULT_PAYMENT_CONFIG, ...(remoteConfig as Partial<AdminPaymentConfig>) };\n    setStored(STORAGE_KEYS.PAYMENT_CONFIG, config);\n    return config;\n  }\n\n  static async savePaymentConfig(config: AdminPaymentConfig, adminUserId?: string): Promise<{ success: boolean; message: string; config?: AdminPaymentConfig }> {\n    setStored(STORAGE_KEYS.PAYMENT_CONFIG, config);\n    const supabase = getSupabase();\n    if (!supabase || !adminUserId) return { success: true, message: 'Tersimpan di perangkat.', config };\n    const { data, error } = await supabase.rpc('custom_save_payment_config', {\n      p_admin_user_id: adminUserId,\n      p_config: config,\n    });\n    if (error || !data?.success) return { success: false, message: error?.message || data?.message || 'Gagal menyimpan pengaturan ke server.' };\n    const saved = (data.config || config) as AdminPaymentConfig;\n    setStored(STORAGE_KEYS.PAYMENT_CONFIG, saved);\n    return { success: true, message: data.message || 'Berhasil disimpan.', config: saved };\n  }\n'''
s = s.replace(old, new, 1)
store.write_text(s)

s = admin.read_text()
s = s.replace("import React, { useState } from 'react';", "import React, { useEffect, useState } from 'react';", 1)
s = s.replace("import { BeresinDataStore } from '../lib/supabase';", "import { BeresinDataStore } from '../lib/supabase';\nimport { useAuth } from '../context/AuthContext';", 1)
s = s.replace("  const [config, setConfig] = useState<AdminPaymentConfig>(() => BeresinDataStore.getPaymentConfig());", "  const { currentUser } = useAuth();\n  const [config, setConfig] = useState<AdminPaymentConfig>(() => BeresinDataStore.getPaymentConfig());\n  const [isSaving, setIsSaving] = useState(false);", 1)
old = '''  const handleSave = (e: React.FormEvent) => {\n    e.preventDefault();\n    BeresinDataStore.savePaymentConfig(config);\n    setSuccessMessage('Pengaturan Kartu Bank & Kontak WhatsApp berhasil disimpan!');\n    onSaved?.();\n    setTimeout(() => {\n      setSuccessMessage('');\n    }, 3000);\n  };'''
if old not in s:
    raise SystemExit('admin save handler missing')
new = '''  const handleSave = async (e: React.FormEvent) => {\n    e.preventDefault();\n    if (!currentUser?.id || isSaving) return;\n    setIsSaving(true);\n    const result = await BeresinDataStore.savePaymentConfig(config, currentUser.id);\n    setIsSaving(false);\n    if (!result.success) { window.alert(result.message); return; }\n    if (result.config) setConfig(result.config);\n    setSuccessMessage('Pengaturan Kartu Bank & Kontak WhatsApp berhasil disimpan di server!');\n    onSaved?.();\n    setTimeout(() => setSuccessMessage(''), 3000);\n  };'''
s = s.replace(old, new, 1)
s = s.replace("whatsapp_number: '6281234567890'", "whatsapp_number: '628136732365'")
s = s.replace("bank_name: 'BCA (Bank Central Asia)'", "bank_name: 'DANA'")
s = s.replace("bank_account_number: '887012345678'", "bank_account_number: '081224405119'")
s = s.replace("bank_account_holder: 'BERESIN OFFICIAL'", "bank_account_holder: 'Hesti Kurnia'")
s = s.replace("      BeresinDataStore.savePaymentConfig(defaultConfig);\n      setConfig(defaultConfig);", "      if (!currentUser?.id) return;\n      void BeresinDataStore.savePaymentConfig(defaultConfig, currentUser.id).then(result => {\n        if (!result.success) window.alert(result.message);\n        else setConfig(result.config || defaultConfig);\n      });")
marker = "  const testWaLink = BeresinDataStore.getWhatsAppLink('Tes pesan dari Admin BERESIN');"
if marker not in s:
    raise SystemExit('admin test link marker missing')
s = s.replace(marker, """  useEffect(() => {\n    let active = true;\n    void BeresinDataStore.loadPaymentConfig().then(remote => { if (active) setConfig(remote); });\n    return () => { active = false; };\n  }, []);\n\n""" + marker, 1)
admin.write_text(s)

s = qris.read_text()
old = '''  useEffect(() => {\n    if (isOpen) {\n      setPaymentConfig(BeresinDataStore.getPaymentConfig());\n    }\n  }, [isOpen]);'''
if old not in s:
    raise SystemExit('QRIS config effect missing')
s = s.replace(old, '''  useEffect(() => {\n    if (!isOpen) return;\n    let active = true;\n    void BeresinDataStore.loadPaymentConfig().then(remote => { if (active) setPaymentConfig(remote); });\n    return () => { active = false; };\n  }, [isOpen]);''', 1)
qris.write_text(s)

s = app.read_text()
marker = '''  useEffect(() => {\n    refreshData();\n  }, [currentUser, role]);'''
if marker not in s:
    raise SystemExit('App refresh marker missing')
if 'setPaymentConfigVersion' not in s:
    lines = s.splitlines()
    idx = next((i for i, line in enumerate(lines) if 'proofPreviewName' in line and 'useState' in line), None)
    if idx is None:
        raise SystemExit('App payment state marker missing')
    lines.insert(idx + 1, "  const [, setPaymentConfigVersion] = useState(0);")
    s = '\n'.join(lines) + '\n'
s = s.replace(marker, marker + '''\n\n  useEffect(() => {\n    void BeresinDataStore.loadPaymentConfig().then(() => setPaymentConfigVersion(v => v + 1));\n  }, [currentUser?.id]);''', 1)
app.write_text(s)

s = landing.read_text()
if "../lib/supabase" not in s:
    marker = "import { ServiceItem } from '../types';"
    if marker not in s:
        raise SystemExit('Landing import marker missing')
    s = s.replace(marker, marker + "\nimport { BeresinDataStore } from '../lib/supabase';", 1)
s = s.replace("  const WHATSAPP_NUMBER = '08136732365';\n  const WHATSAPP_LINK = 'https://wa.me/628136732365?text=Halo%20Admin%20BERESIN,%20saya%20mau%20konsultasi%20jasa%20tugas%20dan%20voucher';", "  const WHATSAPP_NUMBER = BeresinDataStore.getPaymentConfig().whatsapp_number;\n  const WHATSAPP_LINK = BeresinDataStore.getWhatsAppLink('Halo Admin BERESIN, saya mau konsultasi jasa tugas dan voucher');")
landing.write_text(s)

s = seo.read_text()
if "../lib/supabase" not in s:
    marker = "import React, { useEffect, useState } from 'react';"
    if marker not in s:
        raise SystemExit('SEO import marker missing')
    s = s.replace(marker, marker + "\nimport { BeresinDataStore } from '../lib/supabase';", 1)
s = s.replace("  const WHATSAPP_NUMBER = '08136732365';", "  const WHATSAPP_NUMBER = BeresinDataStore.getPaymentConfig().whatsapp_number;")
s = s.replace("  const whatsappUrl = `https://wa.me/628136732365?text=${whatsappMessage}`;", "  const whatsappUrl = BeresinDataStore.getWhatsAppLink(whatsappMessage);")
seo.write_text(s)
