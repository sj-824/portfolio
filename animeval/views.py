from django.shortcuts import render, redirect, get_list_or_404, get_object_or_404
from django.http import Http404
from django.urls import reverse_lazy
from django.views import generic
from django.contrib import messages
from django.contrib.auth import login, authenticate, get_user_model, logout
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (LoginView, LogoutView)
from .forms import ProfileForm, ReviewForm, CreateComment, CreateReply
from accounts.models import User
from .models import ProfileModel, ReviewModel, Counter, AnimeModel, AccessReview, Comment, ReplyComment, Like
import requests
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from django.http import HttpResponse
import io
import math
from django.db.models import Q
from django.db.models import Avg
from datetime import datetime, timedelta
from itertools import groupby
from django.http import Http404, HttpResponseBadRequest
# Create your views here.
        
class OnlyMypageMixin(UserPassesTestMixin):
    raise_expection = True

    def test_func(self):
        profile = ProfileModel.objects.get (user = self.request.user)
        return profile.pk == self.kwargs['pk']

class CreateProfile(LoginRequiredMixin,generic.CreateView):
    template_name = 'animeval/create_profile.html'
    model = ProfileModel
    form_class = ProfileForm
    success_url = reverse_lazy ('animeval:home')

    def form_valid(self,form):
        Counter.objects.create(user = self.request.user)
        profile = form.save(commit = False)
        profile.user = self.request.user
        profile.save()
        return super().form_valid(form)

class UpdateProfile(LoginRequiredMixin,OnlyMypageMixin,generic.UpdateView):
    template_name = 'animeval/update_profile.html'
    model = ProfileModel
    form_class = ProfileForm
    success_url = reverse_lazy ('animeval:home')

    def form_valid(self, form):
        messages.success(self.request, 'プロフィールを更新しました')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'プロフィールの更新に失敗しました')
        return super().form_invalid(form)

class RecAnime:

    def genre_count(self,request):
        # 数字とジャンルを紐付け
        genre = {
        1:'SF',
        2:'ファンタジー',
        3:'コメディ',
        4:'バトル',
        5:'恋愛',
        6:'スポーツ',
        7:'青春',
        8:'戦争',
        }

        # ユーザーの各ジャンルのアクセス数を取得
        counter = Counter.objects.get(user = request.user)
        genre_counter = counter.counter
        top_genre = genre[genre_counter.index(max(genre_counter)) + 1]  # アクセス数の最も多いジャンルを取得

        return top_genre

    def get_rec_anime(self,request):
        reviews = ReviewModel.objects.all()
        animes = AnimeModel.objects.all()
        user_access_review = AccessReview.objects.select_related('review').filter(user = request.user)

        top_genre = self.genre_count(request)
        access_animes = []
        
        for review in user_access_review:
            anime = review.review.anime
            if anime.genre == top_genre and not anime in access_animes:
                access_animes.append(anime)
        
        access_anime_evaluation_sum = [0,0,0,0,0]
        for anime in access_animes:
            anime_reviews = reviews.filter(anime = anime)
            anime_evaluation_sum = [0,0,0,0,0]

            for review in anime_reviews:
                anime_evaluation_sum = np.array(anime_evaluation_sum) + np.array(review.evaluation)
            anime_evaluation_ave = [n/anime_reviews.count() for n in anime_evaluation_sum]

            access_anime_evaluation_sum = np.array(access_anime_evaluation_sum) + np.array(anime_evaluation_ave)
        
        access_anime_evaluation_ave = [n/len(access_animes) for n in access_anime_evaluation_sum]  # アクセスしたアニメレビュー全ての平均値

        anime_list = {}
        for anime in animes.filter(genre = top_genre):
            if not anime in access_animes:
                anime_review = reviews.filter(anime = anime)
                top_genre_anime_evaluation_sum = [0,0,0,0,0]

                if anime_review.exists():
                    for review in anime_review:
                        top_genre_anime_evaluation_sum = np.array(top_genre_anime_evaluation_sum) + np.array(review.evaluation)
                    top_genre_anime_evaluation_ave = [n/anime_review.count() for n in top_genre_anime_evaluation_sum]

                    evaluation_sub = np.array(top_genre_anime_evaluation_ave) - np.array(access_anime_evaluation_ave)
                    evaluation_sqr = map(lambda x : x**2, evaluation_sub)
                    d = math.sqrt(sum(evaluation_sqr))

                    anime_list[anime] = d
        
        context2 = {}
        if anime_list:
            rec_anime = min(anime_list, key = anime_list.get)
            review_count = ReviewModel.objects.filter(anime = rec_anime).count()
            rec_anime_reviews = ReviewModel.objects.filter(anime = rec_anime).order_by('?')[:3]
            rec_anime_rank = self.anime_rank(rec_anime)
            context2 = {'rec_anime' : rec_anime, 'rec_anime_reviews' : rec_anime_reviews, 'rec_anime_rank' : rec_anime_rank, 'review_count' : review_count}
    
        return context2
    
    def anime_rank(self,rec_anime):
        anime_rank = {}
        anime_list = AnimeModel.objects.all()
        for anime in anime_list:
            review_list = ReviewModel.objects.filter(anime = anime)
            review_eval_sum = 0
            for review in review_list:
                review_eval_sum += review.evaluation_ave
            try:
                anime_review_ave = review_eval_sum/review_list.count()
                anime_rank[anime.title] = anime_review_ave
            except ZeroDivisionError:
                pass
        anime_sort = sorted(anime_rank.items(), reverse=True, key = lambda x : x[1])
        ranking = [anime_sort.index(item) for item in anime_sort if rec_anime.title in item[0]]
        return ranking[0] + 1

    def anime_ranking(self,request):
        animes = AnimeModel.objects.all()
        reviews = ReviewModel.objects.all()

        anime_by_popular = {}
        now = datetime.now()
        one_week_ago = now - timedelta(days = 7)
        for anime in animes:
            if reviews.filter(anime = anime).filter(post_date__range = (one_week_ago,now)).exists():
                anime_ave = reviews.filter(anime = anime).filter(post_date__range = (one_week_ago,now)).aggregate(anime_ave = Avg('evaluation_ave'))
                anime_by_popular[anime] = anime_ave['anime_ave']
        anime_by_popular = sorted(anime_by_popular.items(), key=lambda x:x[1], reverse = True)
        anime_list = []
        for anime in anime_by_popular:
            anime_list.append(anime[0])
        context3 = {}
        context3 = {'anime_list' : anime_list[0:3]}
        
        return context3

class Home(LoginRequiredMixin,generic.ListView,RecAnime):
    template_name = 'animeval/home.html'
    queryset = ReviewModel.objects.all().order_by('-post_date')
    paginate_by = 2

    def get(self,request,**kwargs):
        if not ProfileModel.objects.filter(user = self.request.user).exists():
            return redirect('animeval:create_profile')
        return super().get(request,**kwargs)

    def get_context_data(self,**kwargs):
        context = super().get_context_data(**kwargs)
        context.update (kana_list = self.kana_list())
        if self.anime_ranking(self.request):
            context.update(self.anime_ranking(self.request))
        context2 = {'profile' : ProfileModel.objects.get(user = self.request.user)}
        context.update (context2)
        return context
    

    def kana_list(self):
        kana = 'あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをん'
        kana_list = [['あ','い','う','え','お'],['か','き','く','け','こ'],['さ','し','す','せ','そ'],['た','ち','つ','て','と'],['な','に','ぬ','ね','の'],['は','ひ','ふ','へ','ほ'],['ま','み','む','め','も'],['や','ゆ','よ'],['ら','り','る','れ','ろ'],['わ','を','ん']]
        return kana_list

class Analysis(LoginRequiredMixin,generic.TemplateView,RecAnime):
    template_name = 'animeval/analysis.html'
    model = AnimeModel

    def get_context_data(self,**kwargs):
        context = super().get_context_data(**kwargs)
        context2 = {'profile' : ProfileModel.objects.get(user = self.request.user)}
        context.update (context2)
        recanime = RecAnime()
        if recanime.get_rec_anime(self.request):
            context.update(recanime.get_rec_anime(self.request))

        return context

# class MyPage(LoginRequiredMixin,OnlyMypageMixin,generic.DetailView):
#     model = ProfileModel
#     template_name = 'animeval/mypage.html'
#     context_object_name = 'profile'
    
#     def get_reviews(self):
#         reviews = ReviewModel.objects.filter(user = self.object.user).order_by('-post_date')
#         query_word = self.request.GET.get('q')

#         if query_word:
#             reviews = reviews.filter(
#                 Q(review_title__icontains=query_word) |
#                 Q(review_anime_title__icontains = query_word) |
#                 Q(review_content__icontains=query_word)
#             ).order_by('-post_date')

#         context2 = {'reviews' : reviews}
#         return context2
            
#     def get_context_data(self,**kwargs):
#         context = super().get_context_data(**kwargs)
#         context2 = self.get_reviews()
#         context = context.update(context2)
#         return context

@login_required
def mypage(request,pk):
    profile = get_object_or_404(ProfileModel,pk = pk)
    if not request.user == profile.user:
        raise Http404
    reviews = ReviewModel.objects.filter(user = request.user).order_by('-post_date')
    query_word = request.GET.get('q')

    if query_word:
        reviews = reviews.filter(
            Q(review_title__icontains=query_word) |
            Q(anime__title__icontains = query_word) |
            Q(review_content__icontains=query_word)
        ).order_by('-post_date')

    return render(request,'animeval/mypage.html',{'profile':profile,'reviews' : reviews})

class AnimeList(LoginRequiredMixin,generic.ListView):
    template_name = 'animeval/anime_list.html'
    model = AnimeModel
    context_object_name = 'anime_list'

    def get_queryset(self):
        query_word = self.kwargs.get('char')
        return AnimeModel.objects.filter(title_kana__istartswith = query_word)

    def get_context_data(self,**kwargs):
        context = super().get_context_data(**kwargs)
        context.update({'profile' : ProfileModel.objects.get(user = self.request.user)})
        return context

class AnimeDetail(generic.DetailView):
    model = AnimeModel
    template_name = 'animeval/anime_detail.html'
    context_object_name = 'anime'

    def get_context_data(self,**kwargs):
        context = super().get_context_data(**kwargs)
        review_list = ReviewModel.objects.select_related('profile').filter(anime__pk = self.kwargs.get('pk'))
        if review_list.exists():
            context.update({'review_list' : review_list})
        context.update({'profile' : ProfileModel.objects.get(user = self.request.user)})
        return context

@login_required
def create_review(request):
    profile = ProfileModel.objects.get(user = request.user)  # profileを取得

    # アニメタイトルのサジェスト用listの作成
    anime_title_list = []
    animemodel_list = AnimeModel.objects.all()

    for anime in animemodel_list:
        anime_title_list.append(anime.title)

    if request.method == 'POST':
        # AnimeModelに投稿したアニメデータを保存
        anime = request.POST.get('anime')  # 投稿したアニメ名を取得

        if not AnimeModel.objects.filter(title = anime).exists():  # アニメ一覧に該当アニメがない場合
            messages.error(request,'未登録もしくは入力したタイトルに間違いがあります')
            return render (request, 'animeval/create_review.html', {'profile' : profile,'anime_title_list' : anime_title_list})
        
        elif ReviewModel.objects.filter(user = request.user).filter(anime__title = anime).exists():  # すでにレビュー済みのアニメの場合
            messages.error(request,'すでにレビュー済みのタイトルです')
            return render(request, 'animeval/create_review.html', {'profile' : profile,'anime_title_list' : anime_title_list})
        
        else:
            form = ReviewForm(request.POST or None)

            if form.is_valid():
                # Pythonの型に変換
                anime = form.cleaned_data['anime']
                review = form.cleaned_data['review']
                evaluation = [
                    form.cleaned_data['eva_senario'],
                    form.cleaned_data['eva_drawing'],
                    form.cleaned_data['eva_music'],
                    form.cleaned_data['eva_character'],
                    form.cleaned_data['eva_cv']
                ]

                # reviewのタイトルを取得
                split_review = review.splitlines()
                review_title = split_review.pop(0)
                # review_contentの取得
                if request.POST.get('spoiler') == '1':
                    split_review.insert(0,'※ネタバレを含む')
                review_content = '\r\n'.join(split_review)

                # evaluation_aveの取得
                evaluation_ave = sum(evaluation) / len(evaluation)

                # Reviewを作成
                ReviewModel.objects.create(
                    user = request.user,
                    profile = ProfileModel.objects.get(user = request.user),
                    anime = AnimeModel.objects.get(title = anime),
                    review_title = review_title,
                    review_content = review_content,
                    evaluation = evaluation,
                    evaluation_ave = evaluation_ave,
                )

        return redirect('animeval:home')

    else:
        form = ReviewForm

    return render(request,'animeval/create_review.html',{'form' : form, 'profile' : profile, 'anime_title_list' : anime_title_list})

@login_required
def update_review(request,pk):
    review = ReviewModel.objects.get (pk = pk)
    profile = ProfileModel.objects.get(user = request.user)
    
    pre_review = review.review_title + '\n' + review.review_content
    
    if request.method == 'POST':
        content_split = request.POST.get('review_content').splitlines()  # レビュー内容を改行ごとにリスト化
        object.review_title = content_split[0]  # 1行目をレビュータイトルとして保存
        content_split.pop(0)  # レビュー内容の1行目を削除(タイトルを削除)

        # ネタバレの有無による
        if request.POST.get('spoiler') == '1':
            content_split.insert(0,'※ネタバレを含む')  # 1行目にネタバレを含むを挿入
        
        object.review_content = '\r\n'.join(content_split)
        str_values = [request.POST.get('val1'),request.POST.get('val2'),request.POST.get('val3'),request.POST.get('val4'),request.POST.get('val5')]
        object.evaluation_value = '/'.join(str_values)
        int_values = [int(n) for n in str_values]
        object.evaluation_value_ave = sum(int_values)/5
        object.save()
        return redirect('animeval:review_detail', pk = pk)

    return render(request, 'animeval/update_review.html', {'review' : review, 'pre_review' : pre_review, 'profile' : profile})

# def delete_review(request,pk):
#     ReviewModel.objects.get(pk = pk).delete()  # pkから取得し、削除
#     profile_id = ProfileModel.objects.get(user = request.user)  # redirect用のidを取得
#     return redirect('profile', pk = profile_id.id)

class DeleteReview(LoginRequiredMixin,generic.DeleteView):
    model = ReviewModel
    
    def get_success_url(self):
        profile_id = ProfileModel.objects.get(user = self.request.user)
        return reverse_lazy('animeval:profile', kwargs = {'pk' : profile_id})

@login_required
def review_detail(request,pk):
    review = ReviewModel.objects.get(pk = pk)  # reviewを取得
    profile = ProfileModel.objects.get(user = request.user)  # profileを取得

    # レビュー者のその他の投稿をランダムで3つ抽出
    review_list = ReviewModel.objects.filter(user = review.user).order_by('?')[:3]

    # レビューに対するコメントを取得
    comment_list = Comment.objects.filter(review__id = pk).order_by('-created_at')
    reply_list = ReplyComment.objects.filter(comment__review__id = pk).order_by('created_at')

    # アクセスと同時にAccessReviewおよびCounterを更新
    if review.user != request.user:
        if not AccessReview.objects.filter(user = request.user).filter(review = review).exists():
            AccessReview.objects.create(user = request.user, review = review)  # AccessReviewの更新

            # レビューのジャンルをカウントする
            counter = Counter.objects.get(user = request.user)  # 訪問者のCounterを取得
            genre_counter = counter.counter

            # 数字とジャンルを紐付け
            genre = {
            1:'SF',
            2:'ファンタジー',
            3:'コメディ',
            4:'バトル',
            5:'恋愛',
            6:'スポーツ',
            7:'青春',
            8:'戦争',
            }

            anime = review.anime
            genre_num = [key for key, value in genre.items() if value == anime.genre][0]

            for i in range(len(genre_counter) + 1):
                if genre_num == i:
                    genre_counter[i-1] += 1

            counter.counter = genre_counter
            counter.save()

    return render(request, 'animeval/review_detail.html', {
        'review' : review,
        'profile' : profile,
        'review_list' : review_list,
        'comment_list' : comment_list,
        'reply_list' : reply_list})

@login_required
def like(request,review_id,user_id):
    like = Like.objects.filter(review = review_id, user = user_id)
    if like.count() == 0:
        Like.objects.create(
            user = request.user,
            review = ReviewModel.objects.get(pk = review_id)
        )
    else:
        like.delete()
    
    return redirect('animeval:home')

@login_required
def create_comment(request,pk):
    profile = ProfileModel.objects.get(user = request.user)
    if request.method == 'POST':
        form = CreateComment(request.POST)
        if form.is_valid():
            object = form.save(commit = False)
            object.user = request.user
            object.review = ReviewModel.objects.get(pk = pk)
            object.save()
            return redirect('animeval:review_detail', pk = pk)
    else:
        return render(request, 'animeval/create_comment.html', {'profile' : profile})

@login_required
def create_reply(request,pk):
    profile = ProfileModel.objects.get(user = request.user)
    if request.method == 'POST':
        form = CreateReply(request.POST)
        if form.is_valid():
            object = form.save(commit = False)
            object.user = request.user
            object.comment = Comment.objects.get (pk = pk)
            object.save()
            return redirect('animeval:review_detail', pk = object.comment.review.pk)
    else:
        return render(request, 'animeval/create_reply.html', {'profile' : profile})

def setPlt(values1,values2,label1,label2):
#######各要素の設定#########
    labels = ['Senario','Drawing','Music','Character','CV']
    angles = np.linspace(0,2*np.pi,len(labels) + 1, endpoint = True)
    rgrids = [0,1,2,3,4,5] 
    rader_values1 = np.concatenate([values1, [values1[0]]])
    rader_values2 = np.concatenate([values2, [values2[0]]])

#######グラフ作成##########
    plt.rcParams["font.size"] = 16
    fig = plt.figure(facecolor='k')
    fig.patch.set_alpha(0)
    ax = fig.add_subplot(1,1,1,polar = True)
    ax.plot(angles, rader_values1, color = 'r', label = label1)
    ax.plot(angles, rader_values2, color = 'b', label = label2)
    cm = plt.get_cmap('Reds')
    cm2 = plt.get_cmap('Blues')
    for i in range(6):
        z = i/5
        rader_value3 = [n*z for n in rader_values1]
        rader_value4 = [n*z for n in rader_values2]
        ax.fill(angles, rader_value3, alpha = 0.5, facecolor = cm(z))
        ax.fill(angles, rader_value4, alpha = 0.5, facecolor = cm2(z))
    ax.set_thetagrids(angles[:-1]*180/np.pi,labels, fontname = 'AppleGothic', color = 'snow', fontweight = 'bold')
    ax.set_rgrids([])
    ax.spines['polar'].set_visible(False)
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    
    ax.legend(bbox_to_anchor = (1.05,1.0), loc = 'upper left')

    for grid_value in rgrids:
        grid_values = [grid_value] * (len(labels) + 1)
        ax.plot(angles, grid_values, color = 'snow', linewidth = 0.5,)
    
    for t in range(0,5):
        ax.text(x = 0,y = t, s = t,color = 'snow')

    ax.set_rlim([min(rgrids), max(rgrids)])
    ax.set_title ('Evaluation', fontname = 'SourceHanCodeJP-Regular', pad = 20, color = 'snow')
    ax.set_axisbelow(True)

def get_image():
    buf = io.BytesIO()
    plt.savefig(buf,format = 'svg',bbox_inches = 'tight',facecolor = 'dimgrey' , transparent = True)
    graph = buf.getvalue()
    buf.close()
    return graph

def get_svg2(request,pk):
    ###レビュー者の評価###
    review = ReviewModel.objects.get(pk = pk)
    values1 = review.evaluation
    label1 = 'Reviewer_Eval'

    ###全体の平均評価###
    review_list = ReviewModel.objects.filter(anime = review.anime)
    review_count = review_list.count()
    values2_sum = [0,0,0,0,0]
    for review in review_list:
        values2_sum = np.array(values2_sum) + np.array(review.evaluation)
    values2 = [n/review_count for n in values2_sum]
    label2 = 'Reviewer_Eval_Ave'
    setPlt(values1,values2,label1,label2)
    svg = get_image()
    plt.cla()
    response = HttpResponse(svg, content_type = 'image/svg+xml')
    return response

def get_svg(request,pk):
    ###########high_similarity_animeの平均評価##################
    rec_anime = AnimeModel.objects.get(pk=pk)
    review_list = ReviewModel.objects.filter(anime = rec_anime)
    count = review_list.count()
    review_values_sum = [0,0,0,0,0]
    for review in review_list:
        review_values_sum = np.array(review_values_sum) + np.array(review.evaluation)
    values1 = [n/count for n in review_values_sum]
    ###########high_similarity_animeの平均評価##################
    access_animes = []
    for ac_review in AccessReview.objects.filter(user = request.user):
        anime = ac_review.review.anime
        if anime in access_animes:
            pass
        else:
            if anime.genre == rec_anime.genre:
                access_animes.append(anime)
    
    # access_animesの評価平均を取得
    ac_evaluation_sum = [0,0,0,0,0]
    for anime in access_animes:
        reviews = ReviewModel.objects.filter(anime = anime)
        evaluation_sum = [0,0,0,0,0]

        for review in reviews:
            evaluation_sum = np.array(evaluation_sum) + np.array(review.evaluation)

        evaluation_ave = [n/reviews.count() for n in evaluation_sum]

        ac_evaluation_sum = np.array(ac_evaluation_sum) + np.array(evaluation_ave)
    
    ac_evaluation_ave = [n/len(access_animes) for n in ac_evaluation_sum]    
    values2 = ac_evaluation_ave
    
    label1 = 'Reviwer_ave'
    label2 = 'Access_ave'
    setPlt(values1,values2,label1,label2)
    svg = get_image()
    plt.cla()
    response = HttpResponse(svg, content_type = 'image/svg+xml')
    return response


    

