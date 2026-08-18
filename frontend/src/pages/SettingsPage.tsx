import { FormEvent, useEffect, useState } from "react";
import {
  Bell,
  CheckCircle2,
  CloudDownload,
  Database,
  HardDrive,
  Moon,
  Palette,
  Server,
  ShieldCheck,
  Sparkles,
  UserPlus,
  Users,
} from "lucide-react";
import { financeApi, RespaldoEstado, Usuario } from "../api";

export default function SettingsPage() {
  const [health, setHealth] = useState<{
    estado: string;
    version: string;
  } | null>(null);
  const [backup, setBackup] = useState<RespaldoEstado | null>(null);
  const [security, setSecurity] = useState<{
    entorno: string;
    listo_publicacion: boolean;
    controles: Record<string, boolean>;
  } | null>(null);
  const [currentUser, setCurrentUser] = useState<Usuario | null>(null);
  const [mfaSetup, setMfaSetup] = useState<{
    secreto: string;
    uri: string;
  } | null>(null);
  const [users, setUsers] = useState<Usuario[]>([]);
  const [canManage, setCanManage] = useState(false);
  const [open, setOpen] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [highContrast, setHighContrast] = useState(
    () => localStorage.getItem("financeos_high_contrast") === "true",
  );
  const [alerts, setAlerts] = useState(
    () => localStorage.getItem("financeos_alerts") !== "false",
  );
  const loadUsers = async () => {
    try {
      setUsers(await financeApi.usuarios());
      setCanManage(true);
    } catch {
      setCanManage(false);
    }
  };
  useEffect(() => {
    Promise.all([
      financeApi.health(),
      financeApi.estadoRespaldo(),
      financeApi.estadoSeguridad(),
      financeApi.authStatus(),
    ]).then(([h, b, s, a]) => {
      setHealth(h);
      setBackup(b);
      setSecurity(s);
      setCurrentUser(a.usuario ?? null);
    });
    void loadUsers();
  }, []);
  useEffect(() => {
    document.documentElement.classList.toggle("high-contrast", highContrast);
    localStorage.setItem("financeos_high_contrast", String(highContrast));
  }, [highContrast]);
  useEffect(() => {
    localStorage.setItem("financeos_alerts", String(alerts));
  }, [alerts]);
  const download = async () => {
    setDownloading(true);
    setMessage("");
    try {
      const blob = await financeApi.descargarRespaldo();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `FinanceOS-respaldo-${new Date().toISOString().slice(0, 10)}.zip`;
      link.click();
      URL.revokeObjectURL(url);
      setMessage("Respaldo creado correctamente");
    } catch (err) {
      setMessage(
        err instanceof Error ? err.message : "No fue posible descargar",
      );
    } finally {
      setDownloading(false);
    }
  };
  const createUser = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    const data = new FormData(event.currentTarget);
    try {
      await financeApi.crearUsuario({
        nombre: String(data.get("nombre")),
        correo: String(data.get("correo")),
        password: String(data.get("password")),
      });
      setOpen(false);
      await loadUsers();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "No fue posible crear el usuario",
      );
    }
  };
  const toggleUser = async (user: Usuario) => {
    setError("");
    try {
      await financeApi.actualizarUsuario(user.id, { activo: !user.activo });
      await loadUsers();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "No fue posible actualizar el usuario",
      );
    }
  };
  const startMfa = async () => {
    setError("");
    try {
      setMfaSetup(await financeApi.prepararMfa());
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "No fue posible preparar MFA",
      );
    }
  };
  const confirmMfa = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    try {
      const result = await financeApi.confirmarMfa(String(data.get("codigo")));
      setMessage(result.mensaje);
      setMfaSetup(null);
      setCurrentUser(
        currentUser ? { ...currentUser, mfa_habilitado: true } : null,
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Código incorrecto");
    }
  };
  return (
    <section className="module-page">
      <div className="settings-title">
        <div>
          <span className="eyebrow text-violet-200">SISTEMA · CONTROL</span>
          <h2>Tu espacio, tus reglas</h2>
          <p>
            Estado técnico, seguridad, usuarios y preferencias de FinanceOS.
          </p>
        </div>
        <span>
          <ShieldCheck />
        </span>
      </div>
      {error && <div className="error-banner">{error}</div>}
      {security && (
        <section
          className={`security-center ${security.listo_publicacion ? "ready" : "local"}`}
        >
          <div>
            <span className="eyebrow">CENTRO DE SEGURIDAD</span>
            <h3>
              {security.listo_publicacion
                ? "Protección de producción activa"
                : "Protección local activa"}
            </h3>
            <p>
              {security.listo_publicacion
                ? "HTTPS, PostgreSQL, correo y sesiones individuales están configurados."
                : "La instalación es segura para desarrollo privado; completa los controles pendientes antes de publicarla."}
            </p>
          </div>
          <div className="security-controls">
            {Object.entries(security.controles).map(([name, active]) => (
              <span className={active ? "active" : ""} key={name}>
                {active ? <CheckCircle2 /> : <ShieldCheck />}
                {name.split("_").join(" ")}
              </span>
            ))}
          </div>
        </section>
      )}
      <div className="settings-layout">
        <div className="settings-column">
          <h3>Estado del sistema</h3>
          <article className="setting-card system-card">
            <span className="setting-icon green">
              <Server />
            </span>
            <div>
              <strong>API FinanceOS</strong>
              <p>Servicio local · versión {health?.version ?? "…"}</p>
            </div>
            <span className="status-chip">
              <i /> {health?.estado === "ok" ? "Operativa" : "Comprobando"}
            </span>
          </article>
          <article className="setting-card">
            <span className="setting-icon violet">
              <Database />
            </span>
            <div>
              <strong>Base de datos</strong>
              <p>
                {backup?.motor?.toUpperCase() ?? "SQLite"} ·{" "}
                {backup
                  ? `${(backup.tamano / 1024).toFixed(1)} KB`
                  : "Calculando…"}
              </p>
            </div>
            <CheckCircle2 className="setting-check" />
          </article>
          <h3>Preferencias</h3>
          <article className="setting-card">
            <span className="setting-icon blue">
              <Moon />
            </span>
            <div>
              <strong>Contraste reforzado</strong>
              <p>Aumenta bordes y legibilidad en todas las pantallas</p>
            </div>
            <button
              aria-label="Cambiar contraste"
              aria-pressed={highContrast}
              onClick={() => setHighContrast((v) => !v)}
              className={`setting-toggle ${highContrast ? "active" : ""}`}
            >
              <i />
            </button>
          </article>
          <article className="setting-card">
            <span className="setting-icon orange">
              <Bell />
            </span>
            <div>
              <strong>Alertas financieras</strong>
              <p>
                {alerts
                  ? "Presupuestos, metas y pagos próximos"
                  : "Alertas visuales desactivadas en este dispositivo"}
              </p>
            </div>
            <button
              aria-label="Cambiar alertas"
              aria-pressed={alerts}
              onClick={() => setAlerts((v) => !v)}
              className={`setting-toggle ${alerts ? "active" : ""}`}
            >
              <i />
            </button>
          </article>
        </div>
        <div className="settings-column">
          <h3>Seguridad y datos</h3>
          <article className="backup-card">
            <div className="backup-visual">
              <HardDrive />
              <span className="backup-pulse" />
            </div>
            <span className="eyebrow">RESPALDO LOCAL</span>
            <h3>Protege tu historia financiera</h3>
            <p>
              Genera un ZIP con la base de datos y comprobantes. Tus datos
              permanecen en tu dispositivo.
            </p>
            <div className="backup-meta">
              <span>Última modificación</span>
              <strong>
                {backup?.modificado
                  ? new Date(backup.modificado).toLocaleString("es-CO")
                  : "Sin información"}
              </strong>
            </div>
            <button onClick={() => void download()} disabled={downloading}>
              <CloudDownload />
              {downloading ? "Preparando…" : "Descargar respaldo"}
            </button>
            {message && <small>{message}</small>}
          </article>
          <article className="setting-card intelligence">
            <span className="setting-icon violet">
              <Sparkles />
            </span>
            <div>
              <strong>FinanceOS Intelligence</strong>
              <p>Preparado para recomendaciones con IA en una próxima etapa.</p>
            </div>
          </article>
          <article className="setting-card">
            <span className="setting-icon blue">
              <Palette />
            </span>
            <div>
              <strong>Sistema visual</strong>
              <p>React + Tailwind · experiencia responsive</p>
            </div>
            <CheckCircle2 className="setting-check" />
          </article>
        </div>
      </div>
      <section id="mfa-seguridad" className="mfa-card">
        <span className="setting-icon violet">
          <ShieldCheck />
        </span>
        <div>
          <span className="eyebrow">DOBLE PROTECCIÓN</span>
          <h3>Autenticación multifactor</h3>
          <p>
            {currentUser?.mfa_habilitado
              ? "Activa. Cada inicio de sesión requiere un código temporal."
              : "Añade una segunda barrera con tu aplicación autenticadora. Pulsa Activar MFA, copia la clave en Google o Microsoft Authenticator y confirma el código de seis dígitos."}
          </p>
        </div>
        <button
          className={
            currentUser?.mfa_habilitado ? "user-state active" : "primary-action"
          }
          disabled={currentUser?.mfa_habilitado}
          onClick={() => void startMfa()}
        >
          {currentUser?.mfa_habilitado ? "Protegida" : "Activar MFA"}
        </button>
      </section>
      {canManage && (
        <section id="usuarios-acceso" className="users-panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">
                ACCESO PRIVADO · SOLO ADMINISTRADOR
              </span>
              <h3>Personas con acceso</h3>
              <p>
                Tú administras esta instalación. Crea una cuenta diferente para
                cada persona: nadie podrá consultar, sumar ni modificar
                información financiera ajena.
              </p>
            </div>
            <button className="primary-action" onClick={() => setOpen(true)}>
              <UserPlus /> Crear usuario
            </button>
          </div>
          <div className="users-grid">
            {users.map((user) => (
              <article key={user.id}>
                <span className="user-avatar">
                  <Users />
                </span>
                <div>
                  <strong>{user.nombre}</strong>
                  <p>{user.correo}</p>
                </div>
                <span className={`role-chip ${user.rol}`}>{user.rol}</span>
                <button
                  className={`user-state ${user.activo ? "active" : ""}`}
                  onClick={() => void toggleUser(user)}
                >
                  {user.activo ? "Activo" : "Inactivo"}
                </button>
              </article>
            ))}
          </div>
        </section>
      )}
      {open && (
        <div className="modal-backdrop">
          <form className="account-modal user-modal" onSubmit={createUser}>
            <div className="modal-head">
              <div>
                <span className="eyebrow">ACCESO SEGURO</span>
                <h3>Crear usuario</h3>
              </div>
              <button type="button" onClick={() => setOpen(false)}>
                ×
              </button>
            </div>
            <label>
              Nombre
              <input name="nombre" minLength={2} maxLength={100} required />
            </label>
            <label>
              Correo
              <input name="correo" type="email" required />
            </label>
            <label>
              Contraseña temporal
              <input name="password" type="password" minLength={12} required />
              <small>
                Mínimo 12 caracteres. La persona iniciará sesión con esta clave
                y rol de usuario.
              </small>
            </label>
            <button className="modal-submit" type="submit">
              <UserPlus /> Crear acceso privado
            </button>
          </form>
        </div>
      )}
      {mfaSetup && (
        <div className="modal-backdrop">
          <form className="account-modal mfa-modal" onSubmit={confirmMfa}>
            <div className="modal-head">
              <div>
                <span className="eyebrow">MFA · PASO FINAL</span>
                <h3>Conecta tu autenticador</h3>
              </div>
              <button type="button" onClick={() => setMfaSetup(null)}>
                ×
              </button>
            </div>
            <p>
              Copia esta clave en Google Authenticator, Microsoft Authenticator,
              1Password u otra aplicación TOTP.
            </p>
            <code>{mfaSetup.secreto}</code>
            <label>
              Código de seis dígitos
              <input
                name="codigo"
                inputMode="numeric"
                pattern="[0-9]{6}"
                maxLength={6}
                autoComplete="one-time-code"
                required
              />
            </label>
            <button className="modal-submit" type="submit">
              <ShieldCheck /> Confirmar y proteger
            </button>
          </form>
        </div>
      )}
    </section>
  );
}
