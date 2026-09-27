from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render

from leetify_client import LeetifyError, get_match_history, get_player_data

from .forms import CompareForm, MatchSearchForm, NoteForm, PlayerSearchForm, RegisterForm
from .models import SearchHistory


def index(request):
    return render(request, "index.html")


def register(request):
    if request.user.is_authenticated:
        return redirect("index")
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect("index")
    return render(request, "register.html", {"form": form})


@login_required
def profile(request):
    form = PlayerSearchForm(request.POST or None)
    context = {"form": form, "recent": SearchHistory.objects.filter(user=request.user)[:5]}
    if request.method == "POST" and form.is_valid():
        query = form.cleaned_data["query"]
        try:
            player = get_player_data(query)
            if player:
                context["player"] = player
                SearchHistory.objects.create(user=request.user, query=query)
                context["recent"] = SearchHistory.objects.filter(user=request.user)[:5]
            else:
                context["error"] = "ไม่พบข้อมูลผู้เล่นหรือโปรไฟล์ถูกตั้งเป็นส่วนตัว"
        except LeetifyError as exc:
            context["error"] = str(exc)
    elif request.method == "POST":
        context["error"] = "กรุณาระบุคำค้นที่ไม่เกิน 200 ตัวอักษร"
    if request.headers.get("HX-Request") == "true" and request.method == "POST":
        return render(request, "partials/profile_result.html", context)
    return render(request, "profile.html", context)


@login_required
def matches(request):
    form = MatchSearchForm(request.POST or None)
    context = {"form": form}
    if request.method == "POST" and form.is_valid():
        query = form.cleaned_data["query"]
        try:
            context["matches"] = get_match_history(query, form.cleaned_data["limit"])
            context["query"] = query
            if context["matches"]:
                context["steam64_id"] = context["matches"][0].get("steam64_id")
            if not context["matches"]:
                context["error"] = "ไม่พบประวัติแมตช์ของผู้เล่นนี้"
        except LeetifyError as exc:
            context["error"] = str(exc)
    return render(request, "matches.html", context)


@login_required
def compare(request):
    form = CompareForm(request.POST or None)
    context = {"form": form}
    if request.method == "POST" and form.is_valid():
        try:
            context["player1"] = get_player_data(form.cleaned_data["player1"])
            context["player2"] = get_player_data(form.cleaned_data["player2"])
            if not context["player1"] or not context["player2"]:
                context["error"] = "ไม่พบข้อมูลผู้เล่นหนึ่งคนหรือทั้งสองคน"
        except LeetifyError as exc:
            context["error"] = str(exc)
    return render(request, "compare.html", context)


@login_required
def history(request):
    return render(request, "history.html", {"records": SearchHistory.objects.filter(user=request.user)})


@login_required
def edit_history(request, pk):
    record = get_object_or_404(SearchHistory, pk=pk, user=request.user)
    form = NoteForm(request.POST or None, initial={"note": record.note})
    if request.method == "POST" and form.is_valid():
        record.note = form.cleaned_data["note"]
        record.save(update_fields=["note", "updated_at"])
        return redirect("history")
    return render(request, "history_edit.html", {"record": record, "form": form})


@login_required
def delete_history(request, pk):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    record = get_object_or_404(SearchHistory, pk=pk, user=request.user)
    record.delete()
    return redirect("history")
