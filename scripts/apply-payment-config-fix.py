from pathlib import Path

ROOT = Path('.')
store = ROOT / 'src/lib/supabase.ts'
admin = ROOT / 'src/components/AdminPaymentSettings.tsx'
app = ROOT / 'src/App.tsx'

s = store.read_text()
old = """  static getPaymentConfig(): AdminPaymentConfig {\n    return getStored<AdminPaymentConfig>(STORAGE_KEYS.PAYMENT_CONFIG, DEFAULT_PAYMENT_CONFIG);\n  }\n\n  static savePaymentConfig(config: AdminPaymentConfig): void {\n    setStored(STORAGE_KEYS.PAYMENT_CONFIG, config);\n  }\n"""
new = """  static getPaymentConfig(): AdminPaymentConfig {\n    return getStored<AdminPaymentConfig>(STORAGE_KEYS.PAYMENT_CONFIG, DEFAULT_PAYMENT_CONFIG);\n  }\n\n  static async loadPaymentConfig(): Promise<AdminPaymentConfig> {\n    const supabase = getSupabase();\n    if (!supabase) return this.getPaymentConfig();\n    const { data, error } = await supabase.rpc('custom_get_payment_config');\n    if (error || !data?.success || !data.config) return this.getPaymentConfig();\n    const config = data.config as AdminPaymentConfig;\n    setStored(STORAGE_KEYS.PAYMENT_CONFIG, config);\n    return config;\n  }\n\n  static async savePaymentConfig(config: AdminPaymentConfig, adminUserId?: string): Promise<{ success: boolean; message: string }> {\n    setStored(STORAGE_KEYS.PAYMENT_CONFIG, config);\n    const supabase = getSupabase();\n    if (!supabase || !adminUserId) return { success: true, message: 'Tersimpan di perangkat.' };\n    const { data, error } = await supabase.rpc('custom_save_payment_config', {\n      p_admin_user_id: adminUserId,\n      p_config: config,\n    });\n    if (error || !data?.success) {\n      return { success: false, message: error?.message || data?.message || 'Gagal menyimpan pengaturan ke server.' };\n    }\n    return { success: true, message: data.message || 'Berhasil disimpan.' };\n  }\n"""
if old not in s:
    raise SystemExit('payment methods marker missing')
store.write_text(s.replace(old, new, 1))

s = admin.read_text()
s = s.replace("  const handleSave = (e: React.FormEvent) => {", "  const handleSave = async (e: React.FormEvent) => {")
s = s.replace(
    "    BeresinDataStore.savePaymentConfig(config);\n    setSuccessMessage('Pengaturan Kartu Bank & Kontak WhatsApp berhasil disimpan!');",
    "    const result = await BeresinDataStore.savePaymentConfig(config, BeresinDataStore.getUsers().find(u => u.role === 'ADMIN')?.id);\n    if (!result.success) { window.alert(result.message); return; }\n    setSuccessMessage('Pengaturan Kartu Bank & Kontak WhatsApp berhasil disimpan di server!');",
    1,
)
s = s.replace(
    "      BeresinDataStore.savePaymentConfig(defaultConfig);\n      setConfig(defaultConfig);",
    "      void BeresinDataStore.savePaymentConfig(defaultConfig, BeresinDataStore.getUsers().find(u => u.role === 'ADMIN')?.id);\n      setConfig(defaultConfig);",
    1,
)
admin.write_text(s)

s = app.read_text()
if 'setPaymentConfigVersion' not in s:
    marker = "  const [toastNotification, setToastNotification] = useState<{title: string; message: string} | null>(null);"
    if marker in s:
        s = s.replace(marker, marker + "\n  const [, setPaymentConfigVersion] = useState(0);", 1)

marker = """  useEffect(() => {\n    refreshData();\n  }, [currentUser, role]);"""
if marker not in s:
    raise SystemExit('App refresh marker missing')
addition = marker + """\n\n  useEffect(() => {\n    void BeresinDataStore.loadPaymentConfig().then(() => {\n      setPaymentConfigVersion(v => v + 1);\n    });\n  }, [currentUser?.id]);"""
s = s.replace(marker, addition, 1)
app.write_text(s)
