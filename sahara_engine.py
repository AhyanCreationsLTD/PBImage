import os, subprocess, requests, time, threading
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

BOT_TOKEN = "7683523392:AAEMTWbzvFkm2ZgHBAnO5ZOf4DOsvBX4lJ0"
DB_URL = "https://autoliveytdata-default-rtdb.asia-southeast1.firebasedatabase.app"
STREAM_URL = "rtmp://a.rtmp.youtube.com/live2/"

user_streams = {}

def get_data(path):
    try: return requests.get(f"{DB_URL}/{path}.json").json()
    except: return None

def stop_user_stream(tg_id):
    if tg_id in user_streams:
        del user_streams[tg_id]
    os.system(f"pkill -f {tg_id}")

def handle_stream(tg_id, video_url, s_key, is_paid):
    start_time = time.time()
    
    while True:
        if tg_id not in user_streams: break
            
        try:
            v_url = subprocess.check_output(['yt-dlp', '-g', '-f', 'best', video_url]).decode().strip()
            
            # FFmpeg running in background
            cmd = f"ffmpeg -re -stream_loop -1 -i '{v_url}' -c:v libx264 -preset veryfast -b:v 2500k -f flv {STREAM_URL}{s_key}"
            process = subprocess.Popen(cmd, shell=True)
            user_streams[tg_id] = process
            
            if not is_paid:
                time.sleep(300) # 5 Mins for Free User
                stop_user_stream(tg_id)
                break
            else:
                # Rotation Logic: ১১ ঘণ্টা ৫৫ মিনিট (৪৩১০০ সেকেন্ড) পর অটো রিস্টার্ট
                while process.poll() is None:
                    elapsed = time.time() - start_time
                    if elapsed >= 42900: # 11 Hours 55 Mins
                        print(f"🔄 Rotating stream for {tg_id} to prevent 12h limit...")
                        process.terminate()
                        start_time = time.time() # Reset timer
                        break # ব্রেক করলে বাইরের লুপ আবার নতুন করে FFmpeg শুরু করবে
                    time.sleep(60) # প্রতি মিনিটে চেক করবে
                    
        except Exception as e:
            time.sleep(10)

def start(update, context):
    update.message.reply_text("Sahara 24/7 Engine Active! ✅\n/start_live <link>\n/end_live")

def handle_live(update, context):
    tg_id = str(update.message.chat_id)
    text = update.message.text.strip()
    
    if "youtube.com" in text or "youtu.be" in text:
        user = get_data(f"users_by_tg/{tg_id}")
        if not user: return update.message.reply_text("❌ Connect API First!")
            
        now_ms = int(time.time() * 1000)
        is_paid = user.get('planExpiry', 0) > now_ms
        s_key = user.get('streamKey')
        
        stop_user_stream(tg_id)
        user_streams[tg_id] = True
        
        msg = "🎬 24/7 Stream Active with Auto-Rotation (11h 55m)!" if is_paid else "⏳ Free 5 Min Stream Started"
        update.message.reply_text(msg)
        threading.Thread(target=handle_stream, args=(tg_id, text, s_key, is_paid), daemon=True).start()

def end_live(update, context):
    tg_id = str(update.message.chat_id)
    stop_user_stream(tg_id)
    update.message.reply_text("🛑 Live Stopped.")

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("end_live", end_live))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_live))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
                  
