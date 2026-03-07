export const ES_MESSAGES = {
  "auth.login.badge": "Login",
  "auth.login.error.generic":
    "No fue posible iniciar sesión, intenta nuevamente.",
  "auth.login.fields.password": "Contraseña", // pragma: allowlist secret
  "auth.login.fields.username": "Usuario",
  "auth.login.footer.backToLanding": "Regresa a la landing",
  "auth.login.footer.firstTime": "Primera vez aquí?",
  "auth.login.submit.default": "Entrar",
  "auth.login.submit.pending": "Validando...",
  "auth.login.subtitle":
    "Usa tus credenciales para continuar al panel de bienvenida.",
  "auth.login.title": "Inicia sesión",
  "auth.login.validating.title": "Validando sesión...",
  "landing.badge.portal": "Portal",
  "landing.cta.login": "Ir a login",
  "landing.loading.title": "Cargando portal...",
  "landing.subtitle":
    "Inicia sesión para validar tu cuenta y entrar al panel de bienvenida.",
  "landing.title": "Acceso central a tu aplicación.",
  "routing.protected.error.body":
    "Revisa la conexión con la API e intenta nuevamente.",
  "routing.protected.error.title": "No fue posible validar la sesión",
  "routing.protected.validating.body": "Espera un momento.",
  "routing.protected.validating.title": "Validando sesión...",
  "shared.centeredMessage.stateLabel": "Estado",
  "welcome.badge": "Bienvenida",
  "welcome.greeting": "Hola, {username}",
  "welcome.logout": "Cerrar sesión",
  "welcome.noSession.body": "Vuelve a iniciar sesión.",
  "welcome.noSession.title": "No hay sesión activa",
  "welcome.sessionActive.body":
    "Tu sesión está activa y validada contra la API. Desde aquí puedes continuar al siguiente módulo.",
} as const;

export type UiTextKey = keyof typeof ES_MESSAGES;

const PARAM_PATTERN = /\{(\w+)\}/g;

export const t = (
  key: UiTextKey,
  params?: Record<string, string | number>,
): string => {
  const template = ES_MESSAGES[key];
  if (!params) {
    return template;
  }

  let resolvedText = template;
  for (const [placeholder, paramName] of template.matchAll(PARAM_PATTERN)) {
    if (!paramName) {
      continue;
    }

    const value = params[paramName];
    if (value !== undefined) {
      resolvedText = resolvedText.replace(placeholder, String(value));
    }
  }

  return resolvedText;
};
