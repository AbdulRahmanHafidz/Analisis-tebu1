from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
import openpyxl
import io
from datetime import datetime, timedelta
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.core.paginator import Paginator
from django.utils import timezone
from .models import AnalisaTebu
from .forms import AnalisaTebuForm


def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    else:
        return redirect('login')


from django.views.decorators.csrf import csrf_protect

@csrf_protect
def user_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("dashboard")
        else:
            error_message = "Invalid username or password."
            return render(request, "login.html", {"error_message": error_message})
    return render(request, "login.html")


def user_logout(request):
    logout(request)
    return redirect('login')


@login_required
def update_ph(request, pk):
    analisa = get_object_or_404(AnalisaTebu, pk=pk)
    if request.method == "POST":
        ph_value = request.POST.get("ph")
        try:
            analisa.ph = float(ph_value)
            analisa.save()
        except ValueError:
            pass  # Handle invalid input if necessary
    return redirect("dashboard")


@login_required
def dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')

    tanggal_filter = request.GET.get("tanggal")
    shift = request.GET.get("shift")
    search_no = request.GET.get("search_no")

    # Jika tidak ada tanggal filter, gunakan tanggal hari ini
    if not tanggal_filter:
        tanggal_filter = timezone.localtime().strftime("%Y-%m-%d")

    # Tentukan jam_awal dan jam_akhir berdasarkan shift
    if shift == 'pagi':
        jam_awal = '06:00'
        jam_akhir = '14:00'
    elif shift == 'sore':
        jam_awal = '14:00'
        jam_akhir = '22:00'
    elif shift == 'malam':
        jam_awal = '22:00'
        jam_akhir = '06:00'
    else:
        jam_awal = None
        jam_akhir = None

    if tanggal_filter and jam_awal:
        jam_awal_dt = datetime.strptime(f"{tanggal_filter} {jam_awal}", "%Y-%m-%d %H:%M")
        jam_akhir_dt = datetime.strptime(f"{tanggal_filter} {jam_akhir}", "%Y-%m-%d %H:%M")
        if shift == 'malam':
            jam_akhir_dt += timedelta(days=1)
        data = AnalisaTebu.objects.filter(tanggal__range=(jam_awal_dt, jam_akhir_dt)).order_by("tanggal")
    elif tanggal_filter:
        data = AnalisaTebu.objects.filter(tanggal__date=tanggal_filter).order_by("tanggal")
    else:
        data = AnalisaTebu.objects.all().order_by("tanggal")

    # Filter by search_no (displayed NO)
    if search_no:
        try:
            no = int(search_no)
            if no > 0:
                data = data[no-1:no]
        except (ValueError, IndexError):
            pass

    # rata-rata brix koreksi & pol rata-rata
    if data.exists():
        avg_brix = sum([d.brix_koreksi for d in data]) / data.count()
        avg_pol = sum([d.pol_rata2 for d in data]) / data.count()
    else:
        avg_brix, avg_pol = 0, 0

    # Pagination
    paginator = Paginator(data, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Query params for pagination links
    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']

    return render(request, "dashboard.html", {
        "data": page_obj,
        "avg_brix": round(avg_brix, 2),
        "avg_pol": round(avg_pol, 2),
        "query_params": query_params,
        "current_date": timezone.localtime().strftime("%Y-%m-%d"),
    })


@login_required
def export_analisa_tebu_excel(request):
    tanggal_filter = request.GET.get("tanggal")
    shift = request.GET.get("shift")
    search_no = request.GET.get("search_no")

    # Tentukan jam_awal dan jam_akhir berdasarkan shift
    if shift == 'pagi':
        jam_awal = '06:00'
        jam_akhir = '14:00'
    elif shift == 'sore':
        jam_awal = '14:00'
        jam_akhir = '22:00'
    elif shift == 'malam':
        jam_awal = '22:00'
        jam_akhir = '06:00'
    else:
        jam_awal = None
        jam_akhir = None

    if tanggal_filter and jam_awal:
        jam_awal_dt = datetime.strptime(f"{tanggal_filter} {jam_awal}", "%Y-%m-%d %H:%M")
        jam_akhir_dt = datetime.strptime(f"{tanggal_filter} {jam_akhir}", "%Y-%m-%d %H:%M")
        if shift == 'malam':
            jam_akhir_dt += timedelta(days=1)
        data = AnalisaTebu.objects.filter(tanggal__range=(jam_awal_dt, jam_akhir_dt)).order_by("tanggal")
    elif tanggal_filter:
        data = AnalisaTebu.objects.filter(tanggal__date=tanggal_filter).order_by("tanggal")
    else:
        data = AnalisaTebu.objects.all().order_by("tanggal")

    # Filter by search_no (displayed NO)
    if search_no:
        try:
            no = int(search_no)
            if no > 0:
                data = data[no-1:no]
        except (ValueError, IndexError):
            pass

    # Buat workbook dan sheet
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Analisa Tebu"

    # Header
    headers = ["Tanggal", "Brix", "Suhu (°C)", "Brix Koreksi", "Pol", "Pol Rata-rata", "pH"]
    ws.append(headers)

    # Data
    for d in data:
        ws.append([
            d.tanggal.strftime("%Y-%m-%d %H:%M"),
            d.brix,
            d.suhu,
            d.brix_koreksi,
            d.pol,
            d.pol_rata2,
            d.ph if d.ph is not None else "",
        ])


    # Siapkan response
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    response = HttpResponse(
        content=buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    # Format nama file dengan tanggal
    if tanggal_filter:
        filename = f"Analisa Tebu {tanggal_filter}.xlsx"
    else:
        current_date = timezone.localtime().strftime("%Y-%m-%d")
        filename = f"Analisa Tebu {current_date}.xlsx"

    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@login_required
def edit_analisa(request, pk):
    analisa = get_object_or_404(AnalisaTebu, pk=pk)
    if request.method == "POST":
        analisa.brix = request.POST.get("brix")
        analisa.pol = request.POST.get("pol")
        analisa.suhu = request.POST.get("suhu")
        analisa.save()
        return redirect("dashboard")
    return redirect("dashboard")

@login_required
def hapus_analisa(request, pk):
    analisa = get_object_or_404(AnalisaTebu, pk=pk)
    if request.method == "POST":
        analisa.delete()
        return redirect("dashboard")
    return redirect("dashboard")


@login_required
def tambah_analisa(request):
    if request.method == "POST":
        form = AnalisaTebuForm(request.POST)
        if form.is_valid():
            form.instance.tanggal = timezone.now()
            form.save()
            return redirect("dashboard")
    else:
        form = AnalisaTebuForm()
    return render(request, "tambah.html", {"form": form})
