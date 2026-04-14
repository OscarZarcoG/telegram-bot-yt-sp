# 🎸 Bot descargador para bajo

Bot de Telegram que descarga audio de YouTube o Spotify en MP3, listo para meter a Moises.

## Setup

### 1. Crear el bot en Telegram

1. Abre Telegram y busca `@BotFather`
2. Manda `/newbot`
3. Ponle el nombre que quieras
4. Copia el **token** que te da (algo como `123456:ABC-DEF...`)

### 2. Subir a GitHub

```bash
git init
git add .
git commit -m "init"
git remote add origin https://github.com/TU_USUARIO/TU_REPO.git
git push -u origin main
```

### 3. Deploy en Render

1. Entra a [render.com](https://render.com) y crea una cuenta
2. New → **Background Worker** (NO Web Service, porque el bot no necesita HTTP)
3. Conecta tu repo de GitHub
4. En **Environment Variables** agrega:
   - Key: `TELEGRAM_TOKEN`
   - Value: el token que te dio BotFather
5. Click en **Deploy**

Listo. El bot va a estar corriendo 24/7.

## Uso

Mándale al bot un link de YouTube o Spotify y te regresa el MP3.
