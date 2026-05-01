export const ES_MESSAGES = {
  "admin.common.error.generic": "No fue posible completar la operacion, intenta nuevamente.",
  "admin.common.error.title": "Error del modulo administrador",
  "admin.common.loading": "Cargando modulo administrador...",
  "admin.as.submit": "Asignar",
  "admin.as.pending": "Asignando...",
  "admin.as.rid": "ID de rol",
  "admin.as.uid": "ID de usuario",
  "admin.as.placeholder": "Selecciona un ID.",
  "admin.as.rEmpty": "Sin usuarios directos.",
  "admin.as.rTitle": "Usuarios directos",
  "admin.as.title": "Roles directos",
  "admin.as.uEmpty": "Sin roles directos.",
  "admin.as.uTitle": "Roles directos del usuario",
  "admin.pm.help": "own=propio, tenant=tenant actual, any=global.",
  "admin.pm.list": "Permisos asignados",
  "admin.pm.manual": "Sin roles:manage, usa ID manual.",
  "admin.pm.missing": "Rol fuera del catalogo.",
  "admin.pm.title": "Permisos por rol",
  "admin.roles.actions.delete": "Eliminar rol",
  "admin.roles.actions.delete.confirm": "Eliminar el rol {roleName}?",
  "admin.roles.actions.update": "Guardar rol",
  "admin.roles.actions.update.pending": "Guardando...",
  "admin.roles.card.noParents": "Sin roles padre asignados.",
  "admin.roles.card.noPermissions": "Sin permisos asignados.",
  "admin.roles.card.parents": "Jerarquia de roles",
  "admin.roles.card.permissions": "Permisos del rol",
  "admin.roles.create.name": "Nombre del rol",
  "admin.roles.create.submit": "Crear rol",
  "admin.roles.create.submit.pending": "Creando rol...",
  "admin.roles.create.title": "Crear rol",
  "admin.roles.list.empty": "No hay roles registrados.",
  "admin.roles.parents.add": "Asignar rol padre",
  "admin.roles.parents.remove": "Remover",
  "admin.roles.parents.select": "Selecciona rol padre",
  "admin.roles.permissions.add": "Asignar permiso",
  "admin.roles.permissions.remove": "Quitar",
  "admin.roles.permissions.scope.any": "Alcance: any",
  "admin.roles.permissions.scope.label": "Alcance",
  "admin.roles.permissions.select": "Selecciona permiso",
  "admin.roles.subtitle": "Gestiona roles, jerarquia y permisos predefinidos.",
  "admin.roles.title": "Administracion de roles y permisos",
  "admin.users.actions.delete": "Deshabilitar usuario",
  "admin.users.actions.delete.confirm": "Deshabilitar al usuario {username}?",
  "admin.users.actions.edit": "Editar usuario",
  "admin.users.columns.actions": "Acciones",
  "admin.users.columns.roles": "Roles",
  "admin.users.columns.status": "Estado",
  "admin.users.columns.username": "Usuario",
  "admin.users.create.password": "Contrasena", // pragma: allowlist secret
  "admin.users.create.roles": "Roles",
  "admin.users.create.submit": "Crear usuario",
  "admin.users.create.submit.pending": "Creando usuario...",
  "admin.users.create.title": "Crear usuario",
  "admin.users.create.username": "Username",
  "admin.users.edit.cancel": "Cancelar",
  "admin.users.edit.currentPassword": "Contrasena actual", // pragma: allowlist secret
  "admin.users.edit.disabled": "Usuario deshabilitado",
  "admin.users.edit.newPassword": "Nueva contrasena", // pragma: allowlist secret
  "admin.users.edit.roles": "Roles",
  "admin.users.edit.submit": "Guardar cambios",
  "admin.users.edit.submit.pending": "Guardando...",
  "admin.users.edit.title": "Editar usuario",
  "admin.users.edit.username": "Username",
  "admin.users.list.empty": "No hay usuarios registrados.",
  "admin.users.list.title": "Usuarios",
  "admin.users.roles.hidden.error": "Los controles de roles estan ocultos porque no fue posible cargar el catalogo.",
  "admin.users.roles.hidden.permission":
    "Los controles de roles estan ocultos porque esta sesion no puede consultar el catalogo de roles.",
  "admin.users.roles.loading": "Cargando catalogo de roles para esta vista...",
  "admin.users.status.active": "Activo",
  "admin.users.status.disabled": "Inactivo",
  "admin.users.subtitle":
    "Crea, actualiza y deshabilita usuarios; los controles de roles aparecen cuando el catalogo esta disponible.",
  "admin.users.title": "Administracion de usuarios",
  "auth.login.badge": "Login",
  "auth.login.error.generic": "No fue posible iniciar sesion, intenta nuevamente.",
  "auth.login.fields.password": "Contrasena", // pragma: allowlist secret
  "auth.login.fields.username": "Usuario",
  "auth.login.footer.backToLanding": "Regresa a la landing",
  "auth.login.footer.createAccount": "Crea tu cuenta",
  "auth.login.footer.firstTime": "Primera vez aqui?",
  "auth.login.submit.default": "Entrar",
  "auth.login.submit.pending": "Validando...",
  "auth.login.subtitle": "Usa tus credenciales para continuar al panel de bienvenida.",
  "auth.login.title": "Inicia sesion",
  "auth.login.validating.title": "Validando sesion...",
  "auth.register.badge": "Registro",
  "auth.register.error.generic": "No fue posible crear la cuenta, intenta nuevamente.",
  "auth.register.footer.haveAccount": "Ya tienes cuenta?",
  "auth.register.footer.signIn": "Inicia sesion",
  "auth.register.submit.default": "Crear cuenta",
  "auth.register.submit.pending": "Creando cuenta...",
  "auth.register.subtitle": "Crea un acceso local usando el contrato actual de autenticacion.",
  "auth.register.success.body": "La cuenta {username} quedo lista. Inicia sesion para continuar.",
  "auth.register.success.title": "Cuenta creada",
  "auth.register.title": "Crea tu cuenta",
  "auth.shared.password.hint":
    "La contrasena requiere al menos 8 caracteres, una minuscula, una mayuscula y un numero, y no puede contener el username.", // pragma: allowlist secret
  "auth.shared.username.hint":
    "El username se normaliza a minusculas y solo acepta letras, numeros, punto, guion bajo y guion medio.",
  "auth.validation.password.containsUsername": "La contrasena no puede contener el username.", // pragma: allowlist secret
  "auth.validation.password.length": "La contrasena debe tener al menos 8 caracteres.", // pragma: allowlist secret
  "auth.validation.password.lowercase": "La contrasena debe incluir al menos una letra minuscula.", // pragma: allowlist secret
  "auth.validation.password.number": "La contrasena debe incluir al menos un numero.", // pragma: allowlist secret
  "auth.validation.password.uppercase": "La contrasena debe incluir al menos una letra mayuscula.", // pragma: allowlist secret
  "auth.validation.username.format":
    "El username solo acepta letras minusculas, numeros, punto, guion bajo y guion medio.",
  "auth.validation.username.required": "Ingresa un username.",
  "landing.badge.portal": "Portal",
  "landing.cta.login": "Ir a login",
  "landing.loading.title": "Cargando portal...",
  "landing.subtitle": "Inicia sesion para validar tu cuenta y entrar al panel de bienvenida.",
  "landing.title": "Acceso central a tu aplicacion.",
  "profile.actions.cancel": "Cancelar",
  "profile.badge": "Perfil",
  "profile.currentUser": "Sesion activa para {username}",
  "profile.error.generic": "No fue posible actualizar el perfil, intenta nuevamente.",
  "profile.fields.currentPassword": "Contrasena actual", // pragma: allowlist secret
  "profile.fields.newPassword": "Nueva contrasena", // pragma: allowlist secret
  "profile.fields.username": "Username",
  "profile.password.optional": "Deja ambos campos de contrasena vacios si solo cambiaras el username.",
  "profile.submit.default": "Guardar perfil",
  "profile.submit.pending": "Guardando perfil...",
  "profile.subtitle": "Actualiza tu username y, si lo necesitas, rota tu contrasena actual.",
  "profile.success.body": "La sesion local ya refleja los cambios de {username}.",
  "profile.success.title": "Perfil actualizado",
  "profile.title": "Administra tu cuenta",
  "profile.validation.currentPassword.required":
    "Ingresa la contrasena actual para cambiar la contrasena.", // pragma: allowlist secret
  "profile.validation.newPassword.different":
    "La nueva contrasena debe ser diferente a la actual.", // pragma: allowlist secret
  "profile.validation.newPassword.required":
    "Ingresa la nueva contrasena para completar el cambio.", // pragma: allowlist secret
  "profile.validation.noChanges": "No hay cambios para guardar.",
  "routing.error.body": "No fue posible cargar esta ruta.",
  "routing.error.title": "Error de navegacion",
  "routing.notFound.body": "La ruta solicitada no existe.",
  "routing.notFound.title": "Pagina no encontrada",
  "routing.nav.admin.assignments": "Asignaciones",
  "routing.nav.admin.group": "Administrar",
  "routing.nav.admin.permissions": "Permisos",
  "routing.nav.admin.roles": "Roles",
  "routing.nav.admin.users": "Usuarios",
  "routing.nav.home": "Inicio",
  "routing.nav.menu.toggle": "Abrir menu de navegacion",
  "routing.nav.profile": "Perfil",
  "routing.protected.error.body": "Revisa la conexion con la API e intenta nuevamente.",
  "routing.protected.error.title": "No fue posible validar la sesion",
  "routing.protected.validating.body": "Espera un momento.",
  "routing.protected.validating.title": "Validando sesion...",
  "shared.centeredMessage.stateLabel": "Estado",
  "welcome.badge": "Bienvenida",
  "welcome.greeting": "Hola, {username}",
  "welcome.logout": "Cerrar sesion",
  "welcome.logout.pending": "Cerrando sesion...",
  "welcome.noSession.body": "Vuelve a iniciar sesion.",
  "welcome.noSession.title": "No hay sesion activa",
  "welcome.sessionActive.body":
    "Tu sesion esta activa y validada contra la API. Desde aqui puedes continuar al siguiente modulo.",
} as const;

export type UiTextKey = keyof typeof ES_MESSAGES;

const PARAM_PATTERN = /\{(\w+)\}/g;

export const t = (key: UiTextKey, params?: Record<string, string | number>): string => {
  const template = ES_MESSAGES[key];
  if (!params) {
    return template;
  }

  let resolvedText = template;
  for (const match of template.matchAll(PARAM_PATTERN)) {
    const [placeholder, paramName] = match;
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
