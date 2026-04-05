import random

from django.http import Http404
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from .constants import BOOMERANG_GROUP_NAME
from .decorators import boomerang_member_required
from .models import SopAnswer, SopGameTest, SopQuestion


def _is_boomerang_member(user):
    return user.is_authenticated and user.groups.filter(name=BOOMERANG_GROUP_NAME).exists()


def _session_key(slug):
    return f'sop_quiz_{slug}'


def _clear_quiz_session(request, slug):
    request.session.pop(_session_key(slug), None)


def _build_quiz_payload(test):
    questions = list(
        test.questions.prefetch_related('answers').all()
    )
    if not questions:
        return None
    random.shuffle(questions)
    order = []
    perm = {}
    for q in questions:
        order.append(q.pk)
        aids = [a.pk for a in q.answers.all()]
        random.shuffle(aids)
        perm[str(q.pk)] = aids
    return {'order': order, 'perm': perm, 'idx': 0, 'picked': {}}


def boomerang_sop_hub(request):
    """СОП: для всех — информация; прохождение тестов — только группа Boomerang."""
    if _is_boomerang_member(request.user):
        tests = (
            SopGameTest.objects.annotate(q_count=Count('questions'))
            .filter(q_count__gt=0)
            .order_by('title')
        )
        return render(
            request,
            'homepage/boomerang_sop_list.html',
            {'tests': tests},
        )
    return render(request, 'homepage/boomerang_sop_public.html')


@boomerang_member_required
@require_GET
def boomerang_sop_intro(request, slug):
    test = get_object_or_404(SopGameTest, slug=slug)
    n = test.questions.count()
    if n == 0:
        raise Http404()
    return render(
        request,
        'homepage/boomerang_sop_intro.html',
        {'test': test, 'n_questions': n},
    )


@boomerang_member_required
@require_POST
def boomerang_sop_start(request, slug):
    test = get_object_or_404(SopGameTest, slug=slug)
    payload = _build_quiz_payload(test)
    if not payload:
        raise Http404()
    request.session[_session_key(slug)] = payload
    return redirect('boomerang_sop_play', slug=slug)


@boomerang_member_required
def boomerang_sop_play(request, slug):
    test = get_object_or_404(SopGameTest, slug=slug)
    sk = _session_key(slug)
    data = request.session.get(sk)
    if not data:
        return redirect('boomerang_sop_intro', slug=slug)

    order = data['order']
    idx = data['idx']
    picked = data['picked']

    if request.method == 'POST':
        if idx >= len(order):
            return redirect('boomerang_sop_results', slug=slug)
        qid = order[idx]
        try:
            aid = int(request.POST.get('answer', ''))
        except (TypeError, ValueError):
            aid = None
        valid_ids = set(int(x) for x in data['perm'][str(qid)])
        if aid not in valid_ids:
            return redirect('boomerang_sop_play', slug=slug)
        picked[str(qid)] = aid
        data['idx'] = idx + 1
        request.session[sk] = data
        request.session.modified = True
        if data['idx'] >= len(order):
            return redirect('boomerang_sop_results', slug=slug)
        return redirect('boomerang_sop_play', slug=slug)

    # GET
    if idx >= len(order):
        return redirect('boomerang_sop_results', slug=slug)

    qid = order[idx]
    question = get_object_or_404(SopQuestion, pk=qid, test=test)
    aid_order = [int(x) for x in data['perm'][str(qid)]]
    answers = list(SopAnswer.objects.filter(pk__in=aid_order, question=question))
    by_id = {a.pk: a for a in answers}
    ordered_answers = [by_id[i] for i in aid_order if i in by_id]

    progress = idx + 1
    total = len(order)
    return render(
        request,
        'homepage/boomerang_sop_play.html',
        {
            'test': test,
            'question': question,
            'answers': ordered_answers,
            'progress': progress,
            'total': total,
        },
    )


@boomerang_member_required
@require_GET
def boomerang_sop_results(request, slug):
    test = get_object_or_404(SopGameTest, slug=slug)
    sk = _session_key(slug)
    data = request.session.get(sk)
    if not data:
        return redirect('boomerang_sop_intro', slug=slug)

    order = data['order']
    picked = data['picked']
    if len(picked) < len(order):
        return redirect('boomerang_sop_play', slug=slug)

    correct = 0
    mistakes = []
    for qid in order:
        q = SopQuestion.objects.get(pk=qid)
        right = SopAnswer.objects.filter(question=q, is_correct=True).first()
        chosen_id = picked.get(str(qid))
        chosen = SopAnswer.objects.filter(pk=chosen_id).first() if chosen_id else None
        ok = bool(chosen and chosen.is_correct)
        if ok:
            correct += 1
        else:
            mistakes.append(
                {
                    'question': q,
                    'chosen': chosen,
                    'right': right,
                }
            )

    total = len(order)
    _clear_quiz_session(request, slug)

    return render(
        request,
        'homepage/boomerang_sop_results.html',
        {
            'test': test,
            'correct': correct,
            'total': total,
            'mistakes': mistakes,
        },
    )
