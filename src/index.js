const m3uUrl = "https://raw.githubusercontent.com/zerodayip/Py/refs/heads/main/m3u8/playlist.m3u";
const usersUrl = "https://raw.githubusercontent.com/zerodayip/denemeler/refs/heads/main/users.json";
const webhookUrl = "https://canary.discord.com/api/webhooks/your-webhook-url";

export default {
  async fetch(request, env) {
    return handleRequest(request, env);
  }
}

async function handleRequest(request, env) {
  const url = new URL(request.url);
  const username = url.searchParams.get("username");
  const password = url.searchParams.get("password");
  const ip = request.headers.get("CF-Connecting-IP") || request.headers.get("x-forwarded-for") || "Unknown";

  if (!username || !password) {
    return new Response("Kullanıcı adı ve şifre gerekli!", { status: 400 });
  }

  let usersData;
  try {
    const res = await fetch(usersUrl);
    if (!res.ok) throw new Error("Kullanıcı verisi alınamadı");
    usersData = await res.json();
  } catch (e) {
    return new Response("Kullanıcı verisi alınamadı: " + e.message, { status: 500 });
  }

  // Kullanıcı var mı kontrol
  const user = Object.values(usersData).find(u => u.username === username && u.password === password);
  if (!user) {
    return new Response("Geçersiz kullanıcı adı veya şifre!", { status: 403 });
  }

  // Süre kontrolü
  const now = new Date();
  const expireDate = new Date(user.expire_date);
  if (now > expireDate) {
    return new Response("Token süresi dolmuş!", { status: 403 });
  }

  // KV'den aktiflik kontrolü
  const kvKey = `user_active_${username}`;
  const activeDataRaw = await env.TOKENS_DB.get(kvKey);
  if (activeDataRaw) {
    const activeData = JSON.parse(activeDataRaw);
    if (activeData.ip !== ip) {
      return new Response("Bu kullanıcı başka bir cihazda aktif!", { status: 403 });
    }
    // Aynı IP, devam edebilir
  } else {
    // KV'ye kullanıcıyı aktif olarak kaydet
    await env.TOKENS_DB.put(kvKey, JSON.stringify({ ip, lastUsed: now.toISOString() }));
  }

  // M3U verisini al
  let m3uData;
  try {
    const resM3U = await fetch(m3uUrl);
    if (!resM3U.ok) throw new Error("M3U verisi alınamadı");
    m3uData = await resM3U.text();
  } catch (e) {
    return new Response("M3U verisi alınamadı: " + e.message, { status: 500 });
  }

  // Expire bilgisi ekle
  m3uData = appendExpireInfo(m3uData, expireDate);

  // Discord bildirim gönder (async olarak, cevap gecikmesin)
  sendDiscordNotification(username, ip, "Token kullanıldı", webhookUrl).catch(console.error);

  return new Response(m3uData, {
    headers: { "Content-Type": "text/plain" }
  });
}

function appendExpireInfo(m3uData, expireDate) {
  const expireString = expireDate.toLocaleString("tr-TR", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  });

  const expireInfo = `#EXTINF:-1 tvg-name="BİLGİ" tvg-logo="https://cdn-icons-png.flaticon.com/512/1828/1828970.png" group-title="SON TARİH: ${expireString}",...
http://iptv-info.local/expire`;

  return m3uData.replace(/^#EXTM3U\s*/m, `#EXTM3U\n${expireInfo}\n`);
}

async function sendDiscordNotification(username, ip, title, webhook) {
  const message = {
    embeds: [{
      title,
      description: `Kullanıcı: ${username}\nIP: ${ip}`,
      color: 3066993,
      footer: { text: `IPTV Sistem | ${new Date().toLocaleString()}` }
    }]
  };
  await fetch(webhook, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(message),
  });
}
