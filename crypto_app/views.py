from django.shortcuts import render,redirect
from .models import Contact,EncryptedPath,DecryptedPath
from django.contrib import messages
from django.core.files.storage import Storage
from django.conf import settings
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.core import mail
from django.template.loader import render_to_string , get_template
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives
from datetime import datetime ,date
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout

#importing for encryption
import os , base64
# import cryptography
from cryptography.fernet import Fernet as f 

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import json

with open('crypto_app/info.json', 'r') as myfile:
    data=myfile.read()

obj = json.loads(data)

def home(request):
 
    return render(request, 'crypto_app/index.html')

def encrypt(request):
    user = request.user
    try:
        if request.method == "POST" and user.is_authenticated:
            filename = request.POST.get('ename')
            efile = request.FILES.get('files')
            password = request.POST.get('efile_password')

            if not filename:
                messages.error(request," Filename is Required")
            elif len(filename) < 5 :
                messages.error(request," Filename must be 5 char long...")
            elif len(filename) > 30:
                messages.error(request," Filename must be less than 30 char...")
            elif not efile:
                messages.error(request," File is Required")
            elif efile.size > 104857600:
                messages.error(request," File should not more than 99 MB ")
            elif not password:
                messages.error(request," Password is Required")
            elif len(password) < 6:
                messages.error(request,' Password must be 6 char long..')
            elif len(password) > 20:
                messages.error(request," Password must be less than 20 char....")
            else:
                modified_name = change_name(efile.name)

                file_root,file_ext = os.path.splitext(modified_name)
                fal = Storage.get_alternative_name(request,file_root,file_ext)
            
            
                pat = f'media/encrypt/{modified_name}'


                data = efile.read()
                fl,ext = os.path.splitext(fal)
                fkey = f(p(password))
                enc = fkey.encrypt(data)
                file = f"./media/encrypted_file/{fl[0:]+ext}.en"
                encryptedpath = EncryptedPath(user=user,fpath=file,efilename=filename,password=password)
                encryptedpath.save()
                with open(file,'wb') as encfile:
                    encfile.write(enc)
                    print(file)
                
                subject, from_email, to = 'CryptoFile Encryption', obj['from_mail'], user.email
                now = datetime.now()
                day = date.today()
                d1 = day.strftime("%B %d , %Y")
                html_content = render_to_string('crypto_app/registersend.html', {'name':user.first_name , 'file':filename,'user':user,'time':now,'date':d1,'s':"encrypted"}) # render with dynamic value
                text_content = strip_tags(html_content) # Strip the html tag. So people can see the pure text at least.

                # create the email, and attach the HTML version as well.
                msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
                msg.attach_alternative(html_content, "text/html")
                msg.send()


                messages.success(request," Sucessfully File Encrypted ")
                return redirect('encrypted')
    except:
        messages.error(request," !! Please try a file without special charcters !!")

   
    return render(request, 'crypto_app/encrypt.html')

# def contact(request):
#     if request.method == "POST" :
#         name = request.POST.get('contactname', '')
#         email = request.POST.get('contactemail', '')
#         phone = request.POST.get('contactphone', '')
#         desc = request.POST.get('contactmsg', '')
#         print(name)
#         print(email)
#         print(phone)
#         print(desc)
#         if len(name)<2 or len(email)<3 or len(phone)<10 or len(desc)<5:
#             messages.error(request,"please fill the form correctly")
#         else:
#             contact = Contact(name=name, email=email, phone=phone, desc=desc)
#             contact.save()
#             subject, from_email, to = f'{name} facing some problem with Cryptofile', obj['from_mail'], obj['contact_mail']
    
#             html_content = render_to_string('crypto_app/contactsend.html', {'name':name , 'email':email,'phone':phone,'desc':desc}) # render with dynamic value
#             text_content = strip_tags(html_content) # Strip the html tag. So people can see the pure text at least.

#             # create the email, and attach the HTML version as well.
#             msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
#             msg.attach_alternative(html_content, "text/html")
#             msg.send()
#             messages.success(request," Message  sent Sucessfully ,we will contact you within Hour ")
#             return redirect('/')

           
#     return render(request, 'crypto_app/contact.html')

def decrypt(request):
    user = request.user
    try:
        if request.method == "POST" and user.is_authenticated:
            filename = request.POST.get('name')
            dfile = request.FILES.get('files')
            password = request.POST.get('password')

        
            if not filename:
                messages.error(request," Filename is Required")
            elif len(filename) < 5 :
                messages.error(request," Filename must be 5 char long...")
            elif len(filename) > 30:
                messages.error(request," Filename must be less than 30 char...")
            elif not dfile:
                messages.error(request," File is Required")
            elif dfile.size > 52428800:
                messages.error(request," File should not more than 400MB ")
            elif not password:
                messages.error(request," Password is Required")
            elif len(password) < 6:
                messages.error(request,' Password must be 6 char long..')
            elif len(password) > 20:
                messages.error(request," Password must be less than 20 char....")
            else:
                
                modified_name = change_name(dfile.name)

                file_root,file_ext = os.path.splitext(modified_name)
                fal = Storage.get_alternative_name(request,file_root,file_ext)
                pat = f'media/decrypt/{modified_name}'

                if fal.endswith('.en'):
                    data = dfile.read()
                    fl,ext = os.path.splitext(fal)
                    
                    try:
                        fkey = f(p(password))
                        efile = f"media/decrypted/{fl[0:]}"
                        decryptedpath = DecryptedPath(user=user,fpath=efile,dfilename=filename,password=password)
                        decryptedpath.save()
                        dec = fkey.decrypt(data)
                        with open(efile,'wb') as decfile:
                            decfile.write(dec)
                            print(efile)
                        
                        subject, from_email, to = 'CryptoFile Decryption', obj['from_mail'], user.email
                        now = datetime.now()
                        day = date.today()
                        d1 = day.strftime("%B %d , %Y")
                        html_content = render_to_string('crypto_app/registersend.html', {'name':user.first_name , 'file':filename,'user':user,'time':now,'date':d1,'s':"decrypted"}) # render with dynamic value
                        text_content = strip_tags(html_content) # Strip the html tag. So people can see the pure text at least.

                        # create the email, and attach the HTML version as well.
                        msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
                        msg.attach_alternative(html_content, "text/html")
                        msg.send()

                        messages.success(request," Successfully File Decrypted")
                        return redirect('decrypted')
                    except:
                        messages.error(request," Something wrong with your file. Make sure you entered correct Password!!")
                else :
                    messages.warning(request,"!! Please provide file which endswith '.en' !!")
    except:
        messages.error(request," !! Please try a file without special charcters !!")         


    
   
    return render(request, 'crypto_app/decrypt.html')

def about(request):
    return render(request, 'crypto_app/about.html')

def encrypted(request):
    user = request.user

    if user.is_authenticated:
        ef = EncryptedPath.objects.all().filter(user=user).order_by('-edate')
        ef
        paginator = Paginator(ef,7)
        page_number = request.GET.get('page')
        page_obj =paginator.get_page(page_number)
        context = {'page_obj': page_obj }
    return render(request,'crypto_app/encrypted.html',context)

def decrypted(request):
    user = request.user

    if user.is_authenticated:
        ef = DecryptedPath.objects.all().filter(user=user).order_by('-ddate')
        paginator = Paginator(ef,7)
        page_number = request.GET.get('page')
        page_obj =paginator.get_page(page_number)
        context = {'page_obj': page_obj }
    return render(request,'crypto_app/decrypted.html',context)


def wordenc(request):
    try:
        if request.method == "POST":
            data = request.POST.get('data')
            password = request.POST.get('wpassword')
            if not data:
                messages.error(request," Sentence or word is Required to Encrypt")
            elif not password :
                messages.error(request," Password is Required to Encrypt")
            elif len(password) < 3 :
                messages.error(request," Password must be 3 char long.....")
            else:
                fkey = f(p(password))
                endata = data.encode()
                enc = fkey.encrypt(endata)
                denc = enc.decode()
                print(enc.decode())
                return render(request,'crypto_app/wordenc.html',{'enc':denc,'data':data})
       
    except:
        pass

    return render(request,'crypto_app/wordenc.html')



def worddec(request):
    try:
        if request.method == "POST":
            data = request.POST.get('data')
            password = request.POST.get('wpassword')
            if not data:
                messages.error(request," Sentence or word is Required to Encrypt")
            elif not password :
                messages.error(request," Password is Required to Encrypt")
            elif len(password) < 3 :
                messages.error(request," Password must be 3 char long.....")
            else:
                fkey = f(p(password))
                endata = data.encode()
                enc = fkey.decrypt(endata)
                denc = enc.decode('utf-8')
                print(enc.decode())
                return render(request,'crypto_app/worddec.html',{'enc':denc,'data':data})
    except:
        messages.error(request," Signature incorrect")

    return render(request,'crypto_app/worddec.html')



def p(passwd):
    
    password = passwd.encode() # Convert to type bytes
    salt = b'salt_' # CHANGE THIS - recommend using a key from os.urandom(16), must be of type bytes
    kdf = PBKDF2HMAC(
    algorithm=hashes.SHA256(),
    length=32,
    salt=salt,
    iterations=100000,
    backend=default_backend()
            )
    k = base64.urlsafe_b64encode(kdf.derive(password))
    return k


# handling space in file name
def change_name(filename):
    s = f'{filename}'
    return s.replace(' ','_')
    
def handlesignup(request):
    if request.method =='POST':
        username = request.POST.get('username')
        fname = request.POST.get('userfirstname')
        lname = request.POST.get('userlastname')
        email = request.POST.get('useremail')
        password = request.POST.get('userpassword')
        cpassword = request.POST.get('usercpassword')

        if not username:
            messages.error(request," Username Required")
        elif len(username) < 4:
            messages.error(request," Username must be under characters")
        elif User.objects.filter(username=username).exists():
            messages.error(request," Already User exist. Try Another username")
        elif not fname:
            messages.error(request," First Name Required !!")
        elif len(fname) < 3 or len(fname) > 10:
            messages.error(request,' First Name must be 4 char long or more')
        elif not lname:
            messages.error(request,' Last Name Required..')
        elif len(lname) < 4 or len(lname) > 10:
            messages.error(request,' Last Name must be 4 char long or more')
        elif len(email) < 5 or len(email) < 16:
            messages.error(request,'Email must be 5 char long')
        elif User.objects.filter(email=email).exists():
            messages.error(request," Email Already exist. Try Another Email")
        elif not password:
            messages.error(request," Password Required")
        elif not cpassword:
            messages.error(request," Confirm Password Required")
        elif len(password) < 6 or len(password) > 20:
            messages.error(request,' Password must be 6 char long')
        elif password != cpassword:
            messages.error(request," Password do not match")
            
        else:
            
            myuser = User.objects.create_user(username,email,password)
            myuser.first_name = fname
            myuser.last_name = lname
            myuser.save()

            user = authenticate(username=username,password=password)

            if user is not None:
                login(request,user)
                return redirect('/')
            else:
                messages.error(request,"Invalid Credentials, Please try again")
            
            messages.success(request," Account has been sucessfully created")

        return redirect('/')
    else:
        return HttpResponse(request,'404')


def handlelogin(request):
    if request.method == 'POST':
        loginusername = request.POST['loginusername']
        loginpassword = request.POST['loginpassword']

        user = authenticate(username=loginusername,password=loginpassword)

        if user is not None:
            login(request,user)
            return redirect('/')
        else:
            messages.error(request,"Invalid Credentials, Please try again")
            return redirect('/')


def handlelogout(request):
    # if request.method == 'POST':
    logout(request)
    return redirect('home')