import telethon
from telethon.sync import TelegramClient,events,Button
import sys,os,asyncio,jdatetime,datetime,traceback
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from db import (
    Users,
    Servers,
    Services,
    Categorys,
    send_all,
    Process
)
from xui import xui

admins = [305422039]
token = os.environ.get('TOKEN_BOT') 
api_id = os.environ.get('APP_ID')
api_hash = os.environ.get('APP_HASH')
bot = TelegramClient('3x-ui', api_id, api_hash)

def number_format(num):
    return "{:,}".format(num)

START = [
    [Button.text('خرید سرویس',resize=True)],
    [Button.text('حساب کاربری'),Button.text('پشتیبانی')],
    [Button.text('سرور های فعال')]
]
Back = Button.text('🔙',resize=True)

PANEL = [
    [Button.text('آمار ربات',resize = True),Button.text('ارسال پیام')],
    [Button.text('افزودن سرور'),Button.text('مدیریت کاربر'),Button.text('حذف سرور')],
    [Button.text('مدیریت سرور ها')],
    [Button.text('حذف محصول'),Button.text('مدیریت محصولات'),Button.text('افزودن محصول')],
    [Back]
]
pback = Button.text('برگشت',resize=True)

def ban(func):
    async def decorator(event):
        user = Users.get_or_none(Users.user_id == event.sender_id)
        if user.ban is False:
            return await func(event)
        else :
            return False
    return decorator

async def cancel(user):
    try:
        conv = bot.conversation(int(user))
        await conv.cancel_all()
    except:
        pass

async def SendAll():
    send = send_all.get_or_none()
    info = await bot.get_me()
    if send is not None:
        user = Users.select()
        if send.type == 'SendToAll':
            for i in user.limit(send.limit).offset(send.xsends):
                try:
                    if i.user_id != int(info.id):
                        print(f'sended to : {i.user_id}')
                        await bot.send_message(int(i.user_id),str(send.text))
                        send.active += 1
                except (telethon.errors.rpcerrorlist.UserIsBlockedError,telethon.errors.rpcerrorlist.InputUserDeactivatedError):
                    pass
        elif send.type == 'ForToAll':
            for i in user.limit(send.limit).offset(send.xsends):
                try:
                    if i.user_id != int(info.id):
                        print(f'forwarded to : {i.user_id}')
                        t = await bot.forward_messages(int(i.user_id), int(send.message_id), int(send.user))
                        send.active += 1
                except (telethon.errors.rpcerrorlist.UserIsBlockedError,telethon.errors.rpcerrorlist.InputUserDeactivatedError):
                    pass
        send.xsends += int(send.limit)
        send.save()
        xxx = Users.select().count()
        if int(send.xsends) >= int(xxx):
            zzz = send
            send.delete_instance()
            return await bot.send_message(int(send.user),f'پروسه با موفقیت به اتمام رسید ☑️\n\n● زمان اتمام : {jdatetime.datetime.now().strftime("%H:%M")}\nتعداد ارسال های موفق : {zzz.active}',buttons=PANEL)


@bot.on(events.NewMessage(pattern='^\/[Ss][Tt][Aa][Rr][Tt]$',func=lambda e: e.is_private))
async def start(event):
    await cancel(event.sender_id)
    user = Users.get_or_create(user_id=event.sender_id)
    await event.reply('Hello',buttons=START)

@bot.on(events.NewMessage(pattern='🔙',func=lambda e: e.is_private))
@ban
async def back(event):
    await cancel(event.sender_id)
    await event.reply('به منوی اصلی برگشتید',buttons=START)

@bot.on(events.NewMessage(pattern='حساب کاربری',func=lambda e: e.is_private))
@ban
async def myAccount(event):
    user = Users.get(Users.user_id == event.sender_id)
    await event.reply(f'اطلاعات حساب کاربری شما به شرح زیر اس ت: \nموجودی حساب : {number_format(user.coin)}\nآیدی عددی حساب : {event.sender_id}\nتاریخ عضویت : {user.joinDate}')

@bot.on(events.NewMessage(pattern='پشتیبانی',func=lambda e: e.is_private))
@ban
async def Support(event):
    try:
        async with bot.conversation(event.sender_id, timeout=300) as conv:
            sent = await conv.send_message('پیام خود را ارسال کنید', buttons=Back)
            txt = await conv.get_response()
            if txt.text in ('/start','🔙'):
                return
            for i in admins:
                await txt.forward_to(int(i))
                mention = f'<a href="tg://user?id={event.sender_id}">{event.sender_id}</a>'
                t = f"📨 پیام جدید از کاربر {mention} دریافت شد!\n\n👤 آیدی عددی کاربر : {event.sender_id}\n🏷 نام کاربر : {event.sender.first_name}"
                await event.client.send_message(int(i), t, parse_mode = 'html',buttons=[[Button.inline('پاسخ', f'answer-{event.sender_id}')]])
            return await event.reply('پیام شما ارسال شد!',buttons=START)
    except asyncio.exceptions.TimeoutError:
        await sent.delete()
        return await event.reply('مهلت ارسال پیام به اتمام رسید!', buttons=START)

@bot.on(events.CallbackQuery(pattern=b'answer-(\d+)'))
async def userCallback(event):
    try:
        user_id = event.pattern_match.group(1).decode()
        async with bot.conversation(event.chat.id, timeout=300) as conv:
            sent = await conv.send_message('👈 پیام خود را به صورت یک متن جهت ارسال به کاربر ارسال کنید', buttons=Back)
            txt = await conv.get_response()
            while not txt.text:
                sent = await conv.send_message('❌ فقط متن ارسال کنید', buttons=Back)
                txt = await conv.get_response()
            if txt.text in ('/start','🔙'):
                return
            await bot.send_message(int(user_id), str(txt.text))
            return await event.reply('✅ پیام شما با موفقیت ارسال شد', buttons=START)
    except asyncio.exceptions.TimeoutError:
        await sent.delete()
        return await event.reply('❌ مهلت ارسال پیام به کاربر به اتمام رسید', buttons=START)

@bot.on(events.NewMessage(pattern='سرور های فعال',func=lambda e: e.is_private))
@ban
async def ActiveServers(event):
    key = []
    x = Servers.select().where(Servers.status == True)
    if not x.exists():
        return await event.reply('سرور فعالی موجود نیست!')
    for i in x:
        key.append(Button.inline(str(i.name),'server'))
    await event.reply('لیست سرور های فعال ربات :',buttons=key)

def chunk(list: list, number: int) -> list:
    return [list[i:i+number] for i in range(0, len(list), number)]

@bot.on(events.NewMessage(pattern='خرید سرویس',func=lambda e: e.is_private))
@ban
async def Buy(event):
    key = []
    x = Servers.select().where(Servers.status == True)
    if not x.exists():
        return await event.reply('سرور فعالی جهت ارائه موجود نیست!')
    try:
        async with bot.conversation(event.sender_id, timeout=900) as conv:
            servers = []
            key = []
            for i in Servers.select().where(Servers.status == True):
                servers.append(i.name)
                key.append(Button.text(str(i.name)))
            key = chunk(key,2)
            key.insert(len(key) + 1,[Back])
            sent = await conv.send_message('یک سرور را انتخاب کنید :', buttons=key)
            message = await conv.get_response()
            if message.text == '🔙' : return
            while message.text not in servers:
                sent = await conv.send_message('لطفا از کیبورد زیر یک سرور را انتخاب کنید :')
                message = await conv.get_response()
            plans = []
            key = []
            cate = Categorys.select().where(Categorys.status == True).where(Categorys.server == message.text)
            if cate.exists():
                for i in cate:
                    plans.append(i.name)
                    key.append(Button.text(str(i.name)))
                key = chunk(key,2)
                key.insert(len(key) + 1,[Back])
                sent = await conv.send_message('یک محصول را انتخاب نمایید : ', buttons=key)
                name = await conv.get_response()
                if name.text == '🔙' : return
                while name.text not in plans:
                    sent = await conv.send_message('لطفا از کیبورد زیر یک محصول را انتخاب کنید :')
                    name = await conv.get_response()
                info = Categorys.get(Categorys.name == name.text)
                sent = await conv.send_message(f'نام پلن : {name.text}\nقیمت : {number_format(info.price)} تومان\n جهت خرید بر روی یکی از دکمه های زیر کلیک کنید :', buttons=[
                    [Button.text('کارت به کارت'),Button.text('پرداخت از موجودی')],
                    [Back]
                ])
                res = await conv.get_response()
                if res.text == '🔙' : return
                while res.text not in ('کارت به کارت','پرداخت از موجودی'):
                    sent = await conv.send_message('یک گزینه از کیبورد زیر انتخاب کنید :')
                    res = await conv.get_response()
                seinfo = Servers.get(Servers.name == message.text)
                if res.text == 'پرداخت از موجودی':
                    user = Users.get(Users.user_id == event.sender_id)
                    if user.coin >= info.price:
                        send = await event.reply('درحال پردازش ...')
                        try:
                            address = seinfo.address.split(':')
                            try :
                                server = xui(address[0],seinfo.username,seinfo.password,address[1])
                                server.login()
                            except Exception:
                                server = xui(address[0],seinfo.username,seinfo.password,address[1],True)
                                server.login()
                            time = datetime.datetime.now() + datetime.timedelta(days = int(info.days))
                            inbound = server.addClient(
                                seinfo.service,
                                time.timestamp(),
                                info.size,
                                info.limitip
                            )
                            if inbound['success']:
                                user.coin -= info.price
                                user.save()
                                inbound = inbound['obj']
                                uuid = inbound['uuid']
                                port = seinfo.port
                                remark = seinfo.remark
                                email = inbound['email']
                                Services.create(
                                    id = seinfo.service,
                                    user = event.sender_id,
                                    remark = remark,
                                    expiryTime = time.timestamp(),
                                    total = info.size,
                                    port = port,
                                    protocol = 'vless',
                                    email = email,
                                    limitIp = info.limitip,
                                    price = info.price
                                )
                                link = f'vless://{uuid}@{address[0]}:{port}?type=grpc&serviceName=&security=tls&fp=&alpn=http%2F1.1%2Ch2&allowInsecure=1#{remark}-{email}'
                                await send.delete()
                                mention = f"<a href='tg://user?id={event.sender_id}'>{event.sender_id}</a>"
                                for i in admins:
                                    await bot.send_message(int(i),f'کاربر {mention} یک سرویس خریداری کرد !\nمشخصات سرویس خریداری شده : \nسرور : {seinfo.name}\nنام محصول : {info.name}\nقیمت محصول : {info.price}\nلینک اتصال به محصول : \n<code>{link}</code>',parse_mode='html')
                                return await event.reply(f'سرویس شما با موفقیت ساخته شد!\nلینک اتصال : \n<code>{link}</code>',parse_mode='html',buttons=START)
                            else :
                                await send.delete()
                                return await event.reply('خطایی در ساخت سرویس به وجود آمد!')
                        except Exception:
                            await send.delete()
                            return await event.reply('خطایی در ساخت سرویس به وجود آمد!')
                    else :
                        return await event.reply('موجودی شما کافی نیست',buttons=START)
                elif res.text == 'کارت به کارت':
                    sent = await conv.send_message(f'لطفا مبلغ {number_format(info.price)} تومان به شماره کارت زیر واریز کرده و پس از واریز رسید آن را جهت تایید ارسال نمایید \n\n00000000000000000000\nممد\n10 دقیقه جهت ارسال رسید وقت دارید!',buttons=Back)
                    photo = await conv.get_response()
                    if photo.text == '🔙' : return
                    while photo.media is None:
                        sent = await conv.send_message('لطفا یک عکس ارسال کنید')
                        photo = await conv.get_response()
                    while not hasattr(photo.media,'photo'):
                        sent = await conv.send_message('لطفا یک عکس ارسال کنید 2')
                        photo = await conv.get_response()
                    proc = Process.create(
                        user = event.sender_id,
                        server = seinfo.id,
                        category = info.id,
                        price = info.price
                    )
                    for i in admins:
                        await photo.forward_to(int(i))
                        mention = f"<a href='tg://user?id={event.sender_id}'>{event.sender_id}</a>"
                        await bot.send_message(int(i),f'یک رسید جدید توسط کاربر {mention} ارسال شد\nاطلاعات سرویس درخواستی : \nنام سرور درخواستی : {message.text}\nنوع پلن درخواستی : {name.text}\nقیمت پلن : {number_format(info.price)} تومان\n\nدر صورت تایید بر روی دکمه تایید کلیک کنید :',buttons=[
                            [Button.inline('تایید',f'create-{proc.id}'),Button.inline('رد',f'cancel-{proc.id}')]
                        ],parse_mode='html')       
                    return await event.reply('درخواست شما با موفقیت ثبت شد و پس از تایید ادمین سرویس شما ساخته میشود!',buttons=START)                     
            else :
                return await event.reply('محصولی برای این سرور موجود نیست!',buttons=START)
    except asyncio.exceptions.TimeoutError:
            await sent.delete()
            return await event.reply('فرصت به پایان رسید',buttons=PANEL)
    except Exception as e:
        await event.reply(str(e))

@bot.on(events.CallbackQuery(pattern='(create|cancel)-(.*)',func=lambda e: e.is_private))
async def cart(event):
    data = event.pattern_match.group(1).decode()
    proc = event.pattern_match.group(2).decode()
    proc = Process.get(Process.id == proc)
    if proc.status is False:
        return await event.answer('این سفارش رد شده است!')
    if proc.status is True:
        return await event.answer('این سفارش تایید شده است!')
    if data == 'create':
        info = Categorys.get(Categorys.id == proc.category)
        seinfo = Servers.get(Servers.id == proc.server)
        user = Users.get(Users.user_id == proc.user)
        await event.reply('سفارش مورد نظر با موفقیت تایید شد و کانفیگ برای مشتری ارسال شد!')
        try:
            address = seinfo.address.split(':')
            try :
                server = xui(address[0],seinfo.username,seinfo.password,address[1])
                server.login()
            except Exception:
                server = xui(address[0],seinfo.username,seinfo.password,address[1],True)
                server.login()
            time = datetime.datetime.now() + datetime.timedelta(days = int(info.days))
            inbound = server.addClient(
                seinfo.service,
                time.timestamp(),
                info.size,
                info.limitip
            )
            if inbound['success']:
                inbound = inbound['obj']
                uuid = inbound['uuid']
                port = seinfo.port
                remark = seinfo.remark
                email = inbound['email']
                Services.create(
                    id = seinfo.service,
                    user = event.sender_id,
                    remark = remark,
                    expiryTime = time.timestamp(),
                    total = info.size,
                    port = port,
                    protocol = 'vless',
                    email = email,
                    limitIp = info.limitip,
                    price = info.price
                )
                link = f'vless://{uuid}@{address[0]}:{port}?type=grpc&serviceName=&security=tls&fp=&alpn=http%2F1.1%2Ch2&allowInsecure=1#{remark}-{email}'
                return await bot.send_message(int(proc.user),f'سرویس شما با موفقیت ساخته شد!\nلینک اتصال : \n`{link}`',parse_mode='markdown',buttons=START)
            else :
                return await event.reply('خطایی در ساخت سرویس به وجود آمد!')
        except Exception:
            await event.reply(str(traceback.format_exc()))
            return await event.reply('خطایی در ساخت سرویس به وجود آمد!')
    elif data == 'cancel':
        proc.status = False
        proc.save()
        await event.answer('رد شد!')
        return await bot.send_message(int(proc.user),'سفارش شما توسط مدیران ربات تایید نشد!')

@bot.on(events.CallbackQuery(func=lambda e: e.is_private))
async def query(event):
    data = event.data.decode()
    if data == 'SendToAll':
        if event.sender_id not in admins:
            return
        if send_all.get_or_none() is not None:
            return await event.reply('**⚠️ : یک پروسه در حال اجرا دارید !\n❗️: جهت لغو کردن آن از /cancel استفاده کنید.**')
        try :
            async with bot.conversation(event.sender_id) as conv:
                await (await event.reply('.', buttons=Button.clear())).delete()
                sent = await conv.send_message('✏️ : با استفاده از این بخش می توانید یک پیام را به همه ی کاربران فعال ربات ارسال نمایید!\n\nپیام خود را #ارسال نمایید.', buttons=pback)
                message = await conv.get_response()
                if message.text in ('/panel','panel','پنل','برگشت','/start'):
                    return
                sent = await conv.send_message('✅ : لطفا تعداد کاربری که قصد دارید این پیام در هر 30 ثانیه برای آن ها ارسال شود را ارسال کنید.', buttons=pback)
                count = await conv.get_response()
                if count.text in ('/panel','panel','پنل','برگشت','/start'):
                    return
                while not count.raw_text.isnumeric():
                    sent = await conv.send_message(f'**⚠️ :  مقدار ارسالی فقط باید عدد باشد**', buttons=pback)
                    count = await conv.get_response()
                while int(count.raw_text) <= 99 or int(count.raw_text) >= 501:
                    sent = await conv.send_message('**⚠️ عدد وارد شده باید بیشتر از 100 و کمتر از 500 باشد !**',buttons=pback)
                    count = await conv.get_response()
                send_all.create(
                    text = message.text,
                    user = event.sender_id,
                    message_id = message.id,
                    limit = int(count.raw_text),
                    type = 'SendToAll',
                )
                proc = int(Users.select().count()) / int(count.raw_text)
                if proc >= 1:
                    await event.reply(f'✅ : پروسه ارسال پیام همگانی با موفقیت ارسال شد !\n\n⏰ زمان تقریبی اتمام پروسه : {round(proc)} دقیقه',buttons=PANEL)
                return await SendAll()
        except asyncio.exceptions.TimeoutError:
            await sent.delete()
            return await event.reply('فرصت به پایان رسید',buttons=PANEL)
        except:
            pass
    elif data == 'ForToAll':
        if event.sender_id not in admins:
            return
        if send_all.get_or_none() is not None:
            return await event.reply('**⚠️ : یک پروسه در حال اجرا دارید !\n❗️: جهت لغو کردن آن از /cancel استفاده کنید.**')
        try :
            async with bot.conversation(event.sender_id) as conv:
                await (await event.reply('.', buttons=Button.clear())).delete()
                sent = await conv.send_message('✏️ : با استفاده از این بخش می توانید یک پیام را به همه ی کاربران فعال ربات فوروارد نمایید!\n\nپیام خود را #فوروارد نمایید.', buttons=pback)
                message = await conv.get_response()
                if message.text in ('/panel','panel','پنل','برگشت','/start'):
                    return
                sent = await conv.send_message('✅ : لطفا تعداد کاربری که قصد دارید این پیام در هر 30 ثانیه برای آن ها ارسال شود را ارسال کنید.', buttons=pback)
                count = await conv.get_response()
                if count.text in ('/panel','panel','پنل','برگشت','/start'):
                    return
                while not count.raw_text.isnumeric():
                    sent = await conv.send_message(f'**⚠️ :  مقدار ارسالی فقط باید عدد باشد**', buttons=pback)
                    count = await conv.get_response()
                while int(count.raw_text) <= 99 or int(count.raw_text) >= 501:
                    sent = await conv.send_message('**⚠️ عدد وارد شده باید بیشتر از 100 و کمتر از 500 باشد !**',buttons=pback)
                    count = await conv.get_response()
                x = send_all.create(
                    user = event.sender_id,
                    message_id = message.id,
                    limit = int(count.raw_text),
                    type = 'ForToAll',
                )
                proc = int(Users.select().count()) / int(count.raw_text)
                if proc >= 1:
                    await event.reply(f'✅ : پروسه ارسال پیام همگانی با موفقیت ارسال شد !\n\n⏰ زمان تقریبی اتمام پروسه : {round(proc)} دقیقه',buttons=PANEL)
                return
        except asyncio.exceptions.TimeoutError:
            await sent.delete()
            return await event.reply('فرصت به پایان رسید',buttons=PANEL)
        except Exception as e:
            r  = traceback.format_exc()
            await event.reply(str(r))
    elif data == 'SendUser':
        try:
            async with bot.conversation(event.sender_id) as conv:
                await (await event.reply('.', buttons=Button.clear())).delete()
                sent = await conv.send_message('🆔 ایدی عددی کاربر مورد نظر را ارسال کنید', buttons=pback)
                userid = await conv.get_response()
                while not userid.raw_text.isnumeric():
                    sent = await conv.send_message('‼️ ایدی را به صورت عدد ارسال کنید', buttons=pback)
                    userid = await conv.get_response()
                if Users.get_or_none(Users.user_id == userid.raw_text) is None:
                    return await event.reply('❌ کاربری با این ایدی عددی عضو ربات نیست!', buttons=PANEL)
                sent = await conv.send_message('پیام خود را ارسال کنید', buttons=pback)
                pm = await conv.get_response()
                try:
                    await bot.send_message(int(userid.raw_text), pm)
                except Exception as e:
                    pass
                return await event.reply('پیام شما ارسال شد', buttons=PANEL)
        except asyncio.exceptions.TimeoutError:
            await sent.delete()
            return await event.reply('⚠️ فرصت به پایان رسید\n❗️در صورتی که نیاز به فرصت بیشتری دارید، مراحل را مجدد طی کنید', buttons=PANEL)
        except telethon.errors.common.AlreadyInConversationError as a:
            pass

@bot.on(events.NewMessage(from_users=admins,func=lambda e: e.is_private))
async def admin(event):
    text = event.text
    if text in ('/panel','panel','پنل','برگشت'):
        await cancel(event.sender_id)
        return await event.reply('به پنل مدیریت خوش آمدید :',buttons=PANEL)
    elif text == 'آمار ربات':
        pay = 0
        for i in Services.select():
            pay += i.price 
        await event.reply(f'تعداد کاربران : {number_format(Users.select().count())}\nکل فروش ربات : {number_format(pay)}\nتعداد سرور ها : {Servers.select().count()}\nتعداد سرور های فعال : {Servers.select().where(Servers.status == True).count()}\nتعداد محصولات : {Categorys.select().count()}\nتعداد کل سرویس ها : {Services.select().count()}')
    elif text == 'ارسال پیام':
        key = [[Button.inline('پیام همگانی','SendToAll'),Button.inline('پیام به کاربر','SendUser'),Button.inline('فوروارد همگانی','ForToAll')]]
        return await event.reply('لطفا یک گزینه را انتخاب کنید :',buttons=key)
    elif text == 'مدیریت کاربر':
        try :
            async with bot.conversation(event.chat.id) as conv:
                sent = await conv.send_message(f'🆔 ایدی عددی کاربر مورد نظر را ارسال کنید', buttons=pback)
                uid = await conv.get_response()
                if uid.text in ('/panel','panel','پنل','برگشت','/start'):
                    return
                while not uid.raw_text.isnumeric():
                    sent = await conv.send_message(f'‼️ ایدی را به صورت عدد ارسال کنید', buttons=pback)
                    uid = await conv.get_response()
            user = Users.get_or_none(Users.user_id == uid.raw_text)
            if user is None :
                return await event.reply('❌ کاربری با این ایدی عددی در دیتابیس موجود نیست',buttons=PANEL)
            pays = 0
            secx = Services.select().where(Services.user == uid.raw_text)
            for i in secx:
                pays += int(i.price)
            mention = f"<a href='tg://user?id={user.user_id}'>{user.user_id}</a>"
            if user.ban:
                ban = 'مسدود'
            else :
                ban = 'ازاد'
            key = [
                [Button.inline(str(ban),f'ban-{user.user_id}'),Button.inline('🏷 وضعیت حساب :',f'ban-{user.user_id}')],
                [Button.inline('افزایش موجودی',f'upcoin-{user.user_id}'),Button.inline('کاهش موجودی',f'downcoin-{user.user_id}')],
                ]
            await event.reply(f'👤 اطلاعات حساب شخص {mention}\n\n💰 موجودی حساب : <code>{user.coin}</code> تومان\n💳 کل مبلغ خرید ها : <code>{pays}</code> تومان\n🌐 تعداد سرویس ها : <code>{secx.count()}</code>\n🕰 تاریخ عضویت در ربات : <code>{user.joinDate}</code>',buttons=key,parse_mode='html')
            return await event.reply('پنل مدیریت :',buttons=PANEL)
        except asyncio.exceptions.TimeoutError:
            await sent.delete()
            return await event.reply('وقت تمام شد', buttons=PANEL)
        except telethon.errors.common.AlreadyInConversationError as a:
            pass
    elif text == 'افزودن سرور':
        try :
            async with bot.conversation(event.chat.id) as conv:
                sent = await conv.send_message('آیپی یا دامنه سرور را ارسال کنید (بدون http)', buttons=pback)
                address = await conv.get_response()
                if address.text in ('/panel','panel','پنل','برگشت','/start'):
                    return
                sent = await conv.send_message('پورت سرور را ارسال کنید', buttons=pback)
                port = await conv.get_response()
                if port.text in ('/panel','panel','پنل','برگشت','/start'):
                    return
                sent = await conv.send_message('یوزرنیم ورود را ارسال کنید', buttons=pback)
                username = await conv.get_response()
                if username.text in ('/panel','panel','پنل','برگشت','/start'):
                    return
                sent = await conv.send_message('پسورد ورود را ارسال کنید', buttons=pback)
                password = await conv.get_response()
                if password.text in ('/panel','panel','پنل','برگشت','/start'):
                    return
                sent = await conv.send_message('ایدی اینباند را ارسال کنید', buttons=pback)
                inbound = await conv.get_response()
                if inbound.text in ('/panel','panel','پنل','برگشت','/start'):
                    return
                sent = await conv.send_message('پورت اینباند را ارسال کنید', buttons=pback)
                port2 = await conv.get_response()
                if port.text in ('/panel','panel','پنل','برگشت','/start'):
                    return
                sent = await conv.send_message('ریمارک اینباند را ارسال کنید', buttons=pback)
                remark = await conv.get_response()
                if remark.text in ('/panel','panel','پنل','برگشت','/start'):
                    return
                sent = await conv.send_message('نام سرور را وارد کنید(حهت نمایش به کاربران)', buttons=pback)
                name = await conv.get_response()
                if name.text in ('/panel','panel','پنل','برگشت','/start'):
                    return
            try:
                try :
                    connect = xui(address.text.replace('https://','').replace('http://',''),username.text,password.text,port.text,True)
                    login = connect.login()
                except Exception:
                    connect = xui(address.text.replace('https://','').replace('http://',''),username.text,password.text,port.text)
                    login = connect.login()
                if login['success']:
                    Servers.create(
                        name = name.text,
                        address = f"{address.text.replace('https://','').replace('http://','')}:{port.text}",
                        username = username.text,
                        password = password.text,
                        service = int(inbound.text),
                        port = int(port2.text),
                        remark = remark.text
                    )
                    await event.reply('سرور مورد نظر باموفقیت ثبت شد!',buttons=PANEL)
                else :
                    return await event.reply('اطلاعات وارد شده صحیح نیست',buttons=PANEL)
            except Exception as e:
                await event.reply(str(traceback.format_exc()))
                return await event.reply('خطایی در ثبت سرور به وجود آمد!',buttons=PANEL)
        except asyncio.exceptions.TimeoutError:
            await sent.delete()
            return await event.reply('وقت تمام شد', buttons=PANEL)
        except telethon.errors.common.AlreadyInConversationError as a:
            pass
    elif text == 'افزودن محصول':
        try :
            async with bot.conversation(event.chat.id) as conv:
                sent = await conv.send_message('نام محصول را ارسال کنید', buttons=pback)
                name = await conv.get_response()
                if name.text in ('/panel','panel','پنل','برگشت','/start'):
                    return
                sent = await conv.send_message('لیمیت ایپی محصول را به صورت عدد ارسال کنید', buttons=pback)
                iplimit = await conv.get_response()
                if iplimit.text in ('/panel','panel','پنل','برگشت','/start'):
                    return
                sent = await conv.send_message('مدت زمان محصول را به روز ارسال کنید', buttons=pback)
                day = await conv.get_response()
                if day.text in ('/panel','panel','پنل','برگشت','/start'):
                    return
                sent = await conv.send_message('حجم محصول را به صورت عدد و برحسب گیگ ارسال کنید', buttons=pback)
                size = await conv.get_response()
                if size.text in ('/panel','panel','پنل','برگشت','/start'):
                    return
                sent = await conv.send_message('قیمت محصول را بر حسب تومان ارسال کنید', buttons=pback)
                price = await conv.get_response()
                if price.text in ('/panel','panel','پنل','برگشت','/start'):
                    return
                servers = []
                key = []
                for i in Servers.select():
                    servers.append(i.name)
                    key.append(Button.text(str(i.name)))
                key = chunk(key,2)
                key.insert(len(key) + 1,[pback])
                sent = await conv.send_message('سرور محصول را انتخاب کنید :', buttons=key)
                server = await conv.get_response()
                if server.text in ('/panel','panel','پنل','برگشت','/start'):
                    return
                while server.text not in servers:
                    sent = await conv.send_message('لطفا از کیبورد زیر یک سرور انتخاب کنید :')
                    server = await conv.get_response()
            Categorys.create(
                name = name.text,
                price = int(price.raw_text),
                limitip = int(iplimit.raw_text),
                size = int(size.raw_text),
                days = int(day.raw_text),
                server = server.text,
            )
            return await event.reply('محصول مورد نظر با موفقیت ایجاد شد!',buttons=PANEL)
        except asyncio.exceptions.TimeoutError:
            await sent.delete()
            return await event.reply('وقت تمام شد', buttons=PANEL)
        except telethon.errors.common.AlreadyInConversationError as a:
            pass
        except Exception:
            return await event.reply('خطا!')
    elif text == 'مدیریت سرور ها':
        key = []
        select = Servers.select()
        if not select.exists():
            return await event.reply('سروری اضافه نشده جهت مدیریت!')
        for i in select:
            if i.status:
                status = '✅'
            else :
                status = '❌'
            key.append([Button.inline(str(i.name) , f'pserver-{i.id}'),Button.inline(str(status) , f'pserver-{i.id}')])
        await event.reply('لیست سرور ها به شرح زیر است:\nبا کلیک بر روی نام هر سرور میتوانید فروش ان را خاموش روشن کنید',buttons=key)
    elif text == 'حذف سرور':
        key = []
        select = Servers.select()
        if not select.exists():
            return await event.reply('سروری اضافه نشده جهت حذف!')
        for i in select:
            if i.status:
                status = '✅'
            else :
                status = '❌'
            key.append([Button.inline(str(i.name) , f'delserver-{i.id}')])
        await event.reply('با کلیک بر روی نام هر سرور میتوانید ان را حذف کنید\nبا حذف یک سرور تمامی محصولات ان سرور را هم حذف میکنید!',buttons=key)
    elif text == 'مدیریت محصولات':
        key = []
        select = Servers.select()
        if not select.exists():
            return await event.reply('سروری جهت نمایش محصول ان اضافه نشده است!')
        for i in select:
            key.append([Button.inline(str(i.name) , f'showcate-{i.id}')])
        await event.reply('با کلیک بر روی نام هر سرور میتوانید محصولات ان را مشاهده و مدیریت کنید',buttons=key)
    elif text == 'حذف محصول':
        key = []
        select = Servers.select()
        if not select.exists():
            return await event.reply('سروری جهت حذف محصول ان اضافه نشده است!')
        for i in select:
            key.append([Button.inline(str(i.name) , f'delcategory-{i.id}')])
        await event.reply('با کلیک بر روی نام هر سرور میتوانید محصولات ان را مشاهده و حذف کنید',buttons=key)


@bot.on(events.CallbackQuery(pattern='delserver-(.*)'))
async def pserver(event):
    if event.sender_id not in admins:
        return
    server = event.pattern_match.group(1).decode()
    info = Servers.get_or_none(Servers.id == server)
    if info is None:
        return await event.answer('این سرور حذف شده است!')
    for i in Categorys.select().where(Categorys.server == info.name):
        cate = Categorys.get(Categorys.id == i.id)
        cate.delete_instance()
    info.delete_instance()
    await event.answer('سرور مورد نظر حذف شد!')

@bot.on(events.CallbackQuery(pattern='pserver-(.*)'))
async def pserver(event):
    if event.sender_id not in admins:
        return
    server = event.pattern_match.group(1).decode()
    info = Servers.get(Servers.id == server)
    if info.status:
        info.status = False
    else :
        info.status = True
    info.save()
    key = []
    for i in Servers.select():
        if i.status:
            status = '✅'
        else :
            status = '❌'
        key.append([Button.inline(str(i.name) , f'pserver-{i.id}'),Button.inline(str(status) , f'pserver-{i.id}')])
    await event.edit(buttons=key)

@bot.on(events.CallbackQuery(pattern='(showcate|delcategory)-(.*)'))
async def showcate(event):
    if event.sender_id not in admins:
        return
    data = event.pattern_match.group(1).decode()
    server = event.pattern_match.group(2).decode()
    xinfo = Servers.get(Servers.id == server)
    key = []
    select = Categorys.select().where(Categorys.server == xinfo.name)
    if not select.exists():
        return await event.answer('هیچ محصولی اضافه نشده است!')
    if data == 'showcate':
        txt = f'لیست محصولات سرور {xinfo.name}\nبا کلیک بر روی نام هر محصول میتوانید فروش ان را خاموش روشن کنید'
        for i in select:
            if i.status:
                status = '✅'
            else :
                status = '❌'
            key.append([Button.inline(str(i.name) , f'pcate-{i.id}-{xinfo.name}'),Button.inline(str(status) , f'pcate-{i.id}-{xinfo.name}')])
    else :
        txt = 'با کلیک بر روی نام هر محصول میتوانید آن را حذف کنید!'
        for i in select:
            key.append([Button.inline(str(i.name) , f'delcate-{i.id}')])
    await event.edit(str(txt),buttons=key)

@bot.on(events.CallbackQuery(pattern='pcate-(.*)-(.*)'))
async def pcate(event):
    if event.sender_id not in admins:
        return
    category = event.pattern_match.group(1).decode()
    server = event.pattern_match.group(2).decode()
    info = Categorys.get(Categorys.id == category)
    if info.status:
        info.status = False
    else :
        info.status = True
    info.save()
    key = []
    for i in Categorys.select().where(Categorys.server == server):
        if i.status:
            status = '✅'
        else :
            status = '❌'
        key.append([Button.inline(str(i.name) , f'pcate-{i.id}-{server}'),Button.inline(str(status) , f'pcate-{i.id}-{server}')])
    await event.edit(buttons=key)

@bot.on(events.CallbackQuery(pattern='delcate-(.*)'))
async def delcate(event):
    if event.sender_id not in admins:
        return
    category = event.pattern_match.group(1).decode()
    info = Categorys.get_or_none(Categorys.id == category)
    if info is None:
        return await event.answer('این محصول حذف شده است!')
    info.delete_instance()
    await event.answer('محصول مورد نظر حذف شد!')

@bot.on(events.CallbackQuery(pattern='(upcoin|downcoin)-(.*)'))
async def coin(event):
    if event.sender_id not in admins:
        return
    Type = event.pattern_match.group(1).decode()
    user = event.pattern_match.group(2).decode()
    user = Users.get_or_none(Users.user_id == user)
    if user is None:
        return await event.answer('❌ کاربر وجود ندارد',alert=True)
    else :
        try :
            async with bot.conversation(event.sender_id) as conv:
                if Type == 'upcoin':
                    msg = '➕ مقدار موجودی که قصد دارید به حساب کاربر اضافه شود را ارسال کنید'
                    umsg = 'مبلغ {x} تومان توسط مدیریت به حساب شما اضافه شد!'
                else :
                    msg = '➖ مقدار موجودی که قصد دارید از حساب کاربر کم شود را ارسال کنید'
                    umsg = 'مبلغ {x} تومان توسط مدیریت ربات از حساب شما کسر شد!'
                sent = await conv.send_message(str(msg), buttons=Button.text('برگشت',resize=True))
                coin = await conv.get_response()
                if coin.text in ('/panel','panel','پنل','برگشت','/start'):
                    return
                while not coin.raw_text.isnumeric():
                    sent = await conv.send_message(f'‼️ مبلغ را به صورت عدد ارسال کنید', buttons=Button.text('برگشت',resize=True))
                    coin = await conv.get_response()
                if Type == 'upcoin':
                    user.coin += int(coin.text)
                else :
                    user.coin -= int(coin.text)
                user.save()
                await bot.send_message(int(user.user_id),umsg.format(x = number_format(int(coin.text))))
                return await event.reply('✅ عملیات مورد نظر با موفقیت انجام شد',buttons=PANEL)
        except asyncio.exceptions.TimeoutError:
            await sent.delete()
            return await event.reply('وقت تمام شد', buttons=PANEL)
        except telethon.errors.common.AlreadyInConversationError as a:
            pass
        except Exception as e:
            s = traceback.format_exc()
            await event.reply(str(s))

@bot.on(events.CallbackQuery(pattern='ban-(.*)'))
async def ban(event):
    if event.sender_id not in admins:
        return
    user = event.pattern_match.group(1).decode()
    user = Users.get_or_none(Users.user_id == user)
    if user is None:
        return await event.answer('❌ کاربر وجود ندارد',alert=True)
    else :
        if user.ban:
            x = False
        else :
            x = True
        user.ban = x
        user.save()
        if user.ban:
            ban = 'مسدود'
        else :
            ban = 'ازاد'
        key = [
            [Button.inline(str(ban),f'ban-{user.user_id}'),Button.inline('🏷 وضعیت حساب :',f'ban-{user.user_id}')],
            [Button.inline('افزایش موجودی',f'upcoin-{user.user_id}'),Button.inline('کاهش موجودی',f'downcoin-{user.user_id}')],
        ]
        return await event.edit(buttons=key)

@bot.on(events.NewMessage(pattern='[\/\.]reload',from_users =admins))
async def Reload(event):
    await event.reply('Reloaded Successfully')
    python = sys.executable
    os.execl(python, python, *sys.argv)

scheduler = AsyncIOScheduler(timezone="Asia/Tehran")
scheduler.add_job(SendAll, trigger="interval",seconds=30)
scheduler.start()    

bot.start(bot_token = token)
bot.run_until_disconnected()
