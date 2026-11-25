// Service worker da Maya: recebe as notificações (lembretes) mesmo com o app fechado.
self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (e) => e.waitUntil(self.clients.claim()));

self.addEventListener("push", (evento) => {
  let dados = { titulo: "Maya", texto: "" };
  try { dados = evento.data.json(); } catch { if (evento.data) dados.texto = evento.data.text(); }
  evento.waitUntil(
    self.registration.showNotification(dados.titulo || "Maya", {
      body: dados.texto,
      icon: "/app/icone-192.png",
      badge: "/app/icone-192.png",
    })
  );
});

self.addEventListener("notificationclick", (evento) => {
  evento.notification.close();
  evento.waitUntil(
    self.clients.matchAll({ type: "window" }).then((janelas) => {
      for (const janela of janelas) if ("focus" in janela) return janela.focus();
      return self.clients.openWindow("/");
    })
  );
});
