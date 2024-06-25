import os
import time
import uuid
import csv
import io
from django.shortcuts import render, redirect
from django.http import HttpResponse, FileResponse, Http404
from django.conf import settings
from home.models import FileInfo
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
import shutil
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden
import zipfile

from django.http import JsonResponse
from django.shortcuts import render, reverse
from django.contrib.auth.decorators import login_required
from .models import ChatBot
from django.http import HttpResponseRedirect, JsonResponse
import google.generativeai as genai


def index(request):
    context = {}
    # Add context data here
    # context['test'] = 'OK'
    # Page from the theme 
    return render(request, 'pages/dashboard.html', context=context)

def custom_403_view(request, exception=None):
    return render(request, 'layouts/403.html', status=403)

def convert_bytes_to_mb(size_in_bytes):
    """Convierte el tamaño del archivo de bytes a megabytes."""
    size_in_mb = size_in_bytes / (1024 * 1024)  # 1 MB = 1024 * 1024 bytes
    return size_in_mb


genai.configure(api_key="AIzaSyA0M2ljxoufjlGy7bAGCMqw34217Mw6zag")
#@login_required
def ask_question(request):
    views_dir = os.path.dirname(__file__)
    ins_file_path = os.path.join(views_dir, 'ins.txt')
    
    with open(ins_file_path, "r", encoding='utf-8') as file:
        instruccion = file.read()

    if request.method == "POST":
        text = request.POST.get("text")
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=instruccion,
        )        
        # Verificar si hay un usuario autenticado
        if request.user.is_authenticated:
            chat = model.start_chat()
            response = chat.send_message(text)
            ChatBot.objects.create(text_input=text, gemini_output=response.text, user=request.user)
            response_data = {
                "text": response.text,
            }
        else:
            chat = model.start_chat()
            response = chat.send_message(text)
            response_data = {
                "text": response.text,
            }

        return JsonResponse({"data": response_data})
    else:
        return HttpResponseRedirect(reverse("chat"))

#@login_required
def chat(request):
    user = request.user
    # Verificar si el usuario está autenticado
    if user.is_authenticated:
        chats = ChatBot.objects.filter(user=user)
    else:
        # Usuario no autenticado, manejar el caso apropiadamente
        chats = []

    return render(request, "pages/chatbot.html", {"chats": chats})


def download_all(request):
    media_path = os.path.join(settings.MEDIA_ROOT)
    selected_directory = request.POST.get('directory', '') 
    selected_directory_path = os.path.join(media_path, selected_directory)

    # Crea un archivo zip en memoria
    zip_io = io.BytesIO()
    with zipfile.ZipFile(zip_io, 'w') as zip_file:
        for filename in os.listdir(selected_directory_path):
            file_path = os.path.join(selected_directory_path, filename)
            zip_file.write(file_path, arcname=filename)

    zip_io.seek(0)

    # Crea una respuesta con el archivo zip
    response = FileResponse(zip_io, content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename=t/{selected_directory}.zip'

    return response


def convert_csv_to_text(csv_file_path):
    with open(csv_file_path, 'r') as file:
        reader = csv.reader(file)
        rows = list(reader)

    text = ''
    for row in rows:
        text += ','.join(row) + '\n'

    return text

def get_files_from_directory(directory_path):
    files = []
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        if os.path.isfile(file_path):
            try:
                print( ' > file_path ' + file_path)
                _, extension = os.path.splitext(filename)
                if extension.lower() == '.csv':
                    csv_text = convert_csv_to_text(file_path)
                else:
                    csv_text = ''
                # Recupera la fecha y hora de subida de los metadatos del archivo
                upload_date = time.strftime('%d/%m/%Y %H:%M', time.localtime(os.path.getmtime(file_path)))   
                file_size = os.path.getsize(file_path)
                file_size_mb = convert_bytes_to_mb(file_size)
                files.append({
                    'file': file_path.split(os.sep + 'media' + os.sep)[1],
                    'filename': filename,
                    'file_path': file_path,
                    'csv_text': csv_text,
                    'upload_date': upload_date,
                    'size': file_size_mb,  # Agrega el tamaño del archivo a la información del archivo
                })
            except Exception as e:
                print( ' > ' +  str( e ) )    
    return files

def save_info(request, file_path):
    path = file_path.replace('%slash%', '/')
    if request.method == 'POST':
        FileInfo.objects.update_or_create(
            path=path,
            defaults={
                'info': request.POST.get('info')
            }
        )
    
    return redirect(request.META.get('HTTP_REFERER'))

def get_breadcrumbs(request):
    path_components = [component for component in request.path.split("/") if component]
    breadcrumbs = []
    url = ''

    for component in path_components:
        url += f'/{component}'
        if component == "file-manager":
            component = "media"
        breadcrumbs.append({'name': component, 'url': url})

    return breadcrumbs

@login_required(login_url='/accounts/login/')
def file_manager(request, directory=''):
    media_path = os.path.join(settings.MEDIA_ROOT)
    directories = generate_nested_directory(media_path, media_path)
    # Si el usuario es un administrador, tiene acceso a todos los directorios
    if request.user.is_superuser or directory == '':
        pass
    else:
        # Obtener los nombres de los grupos a los que pertenece el usuario
        user_groups = request.user.groups.values_list('name', flat=True)

        # Si ninguna subcarpeta del directorio está en los grupos del usuario, lanzar una excepción
        if not any(subdir in user_groups for subdir in directory.split('/')):
            raise PermissionDenied("No tienes permiso para acceder a este directorio.")
    selected_directory = directory

    files = []
    selected_directory_path = os.path.join(media_path, selected_directory)
    if os.path.isdir(selected_directory_path):
        files = get_files_from_directory(selected_directory_path)
    breadcrumbs = get_breadcrumbs(request)

    context = {
        'directories': directories, 
        'files': files, 
        'selected_directory': selected_directory,
        'segment': 'file_manager',
        'breadcrumbs': breadcrumbs
    }
    return render(request, 'pages/file-manager.html', context)



def generate_nested_directory(root_path, current_path):
    directories = []
    for name in os.listdir(current_path):
        if os.path.isdir(os.path.join(current_path, name)):
            unique_id = str(uuid.uuid4())
            nested_path = os.path.join(current_path, name)
            nested_directories = generate_nested_directory(root_path, nested_path)
            directories.append({'id': unique_id, 'name': name, 'path': os.path.relpath(nested_path, root_path), 'directories': nested_directories})
    return directories


def delete_file(request, file_path):
    path = file_path.replace('%slash%', '/')
    absolute_file_path = os.path.join(settings.MEDIA_ROOT, path)
    os.remove(absolute_file_path)
    print("File deleted", absolute_file_path)
    return redirect(request.META.get('HTTP_REFERER'))

    
def download_file(request, file_path):
    path = file_path.replace('%slash%', '/')
    absolute_file_path = os.path.join(settings.MEDIA_ROOT, path)
    if os.path.exists(absolute_file_path):
        with open(absolute_file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(absolute_file_path)
            return response
    raise Http404

def upload_file(request):
    media_path = os.path.join(settings.MEDIA_ROOT)
    selected_directory = request.POST.get('directory', '') 
    selected_directory_path = os.path.join(media_path, selected_directory)
    if request.method == 'POST':
        files = request.FILES.getlist('file[]')
        for file in files:
            file_path = os.path.join(selected_directory_path, file.name)
            with open(file_path, 'wb') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
            # Guarda la fecha y hora de subida en los metadatos del archivo
            os.utime(file_path, times=(time.time(), time.time()))
            username = request.user.username  # Obtiene el nombre de usuario

    return redirect(request.META.get('HTTP_REFERER'))

def mk_dir(request):
    media_path = os.path.join(settings.MEDIA_ROOT)
    selected_directory = request.POST.get('directory', '') 
    folder_name = request.POST.get('folder_name', '') 
    folder_path = os.path.join(media_path, selected_directory, folder_name)
    if request.method == 'POST':
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

    # Redirige al directorio recién creado
    return redirect(request.META.get('HTTP_REFERER'))


def delete_dir(request):
    media_path = os.path.join(settings.MEDIA_ROOT)
    selected_directory = request.POST.get('directory', '') 
    folder_path = os.path.join(media_path, selected_directory)
    print(folder_path)
    if request.method == 'POST':
        try:
            if os.path.exists(folder_path):
                # Verifica si el nombre de la carpeta es "media"
                if selected_directory.lower() != '':
                    shutil.rmtree(folder_path)
                else:
                    print("No se puede borrar la carpeta 'media'.")
        except Exception as e:
            print(f"Error al eliminar el directorio: {e}")

    return redirect("/file-manager")


