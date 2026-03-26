"""
Chart generation services using Pandas, Matplotlib, and Seaborn.
Charts are rendered as base64 images for embedding in templates.
"""
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import base64
from io import BytesIO
from datetime import datetime, timedelta
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from django.utils import timezone


# Set consistent style
sns.set_theme(style="whitegrid")
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['axes.facecolor'] = 'white'
plt.rcParams['font.family'] = 'sans-serif'


def fig_to_base64(fig, dpi=100):
    """Convert matplotlib figure to base64 string for HTML embedding."""
    buffer = BytesIO()
    fig.savefig(
        buffer,
        format='png',
        dpi=dpi,
        bbox_inches='tight',
        facecolor='white',
        edgecolor='none',
        transparent=False
    )
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    plt.close(fig)
    return f"data:image/png;base64,{image_base64}"


def generate_win_loss_chart(fights_queryset):
    """
    Generate a donut chart showing Win vs Loss ratio.
    Color scheme: Red for wins, Blue for losses.
    """
    # Get completed fights with results
    completed_fights = fights_queryset.filter(
        status='completed'
    ).exclude(result='').values('result').annotate(count=Count('id'))

    if not completed_fights:
        return None

    # Convert to DataFrame
    df = pd.DataFrame(list(completed_fights))

    if df.empty:
        return None

    # Define colors (red theme with blue accent)
    color_map = {
        'win': '#DC2626',      # Red-600
        'loss': '#3B82F6',     # Blue-500
        'draw': '#F59E0B',     # Amber-500
        'no_contest': '#6B7280'  # Gray-500
    }

    colors = [color_map.get(r, '#9CA3AF') for r in df['result']]

    # Create figure
    fig, ax = plt.subplots(figsize=(6, 6))

    # Create donut chart
    wedges, texts, autotexts = ax.pie(
        df['count'],
        labels=[r.replace('_', ' ').title() for r in df['result']],
        colors=colors,
        autopct='%1.1f%%',
        startangle=90,
        pctdistance=0.75,
        wedgeprops=dict(width=0.5, edgecolor='white')
    )

    # Style the text
    plt.setp(autotexts, size=12, weight='bold', color='white')
    plt.setp(texts, size=11)

    # Add center text
    total = df['count'].sum()
    ax.text(0, 0, f'{total}\nFights', ha='center', va='center',
            fontsize=16, fontweight='bold', color='#374151')

    ax.set_title('Win/Loss Ratio', fontsize=14, fontweight='bold', pad=20)

    return fig_to_base64(fig)


def generate_fights_per_month_chart(fights_queryset, months=12):
    """
    Generate a bar chart showing number of fights per month.
    """
    # Get date range
    end_date = timezone.now()
    start_date = end_date - timedelta(days=months * 30)

    # Aggregate by month
    monthly_fights = fights_queryset.filter(
        scheduled_datetime__gte=start_date,
        status='completed'
    ).annotate(
        month=TruncMonth('scheduled_datetime')
    ).values('month').annotate(
        count=Count('id'),
        wins=Count('id', filter=Q(result='win')),
        losses=Count('id', filter=Q(result='loss'))
    ).order_by('month')

    if not monthly_fights:
        return None

    df = pd.DataFrame(list(monthly_fights))

    if df.empty:
        return None

    df['month_label'] = df['month'].apply(lambda x: x.strftime('%b %Y') if x else '')

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 5))

    # Bar width
    x = range(len(df))
    width = 0.35

    # Create grouped bars
    bars1 = ax.bar([i - width/2 for i in x], df['wins'], width,
                   label='Wins', color='#DC2626', edgecolor='white')
    bars2 = ax.bar([i + width/2 for i in x], df['losses'], width,
                   label='Losses', color='#3B82F6', edgecolor='white')

    ax.set_xlabel('Month', fontsize=11)
    ax.set_ylabel('Number of Fights', fontsize=11)
    ax.set_title('Fights Per Month', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(df['month_label'], rotation=45, ha='right')
    ax.legend()

    # Add value labels on bars
    for bar in bars1:
        height = bar.get_height()
        if height > 0:
            ax.annotate(f'{int(height)}',
                       xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 3), textcoords='offset points',
                       ha='center', va='bottom', fontsize=9)

    for bar in bars2:
        height = bar.get_height()
        if height > 0:
            ax.annotate(f'{int(height)}',
                       xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 3), textcoords='offset points',
                       ha='center', va='bottom', fontsize=9)

    plt.tight_layout()
    return fig_to_base64(fig)


def generate_breed_distribution_chart(fowl_queryset):
    """
    Generate a horizontal bar chart showing breed distribution.
    """
    breed_counts = fowl_queryset.exclude(
        breed=''
    ).exclude(
        breed__isnull=True
    ).values('breed').annotate(
        count=Count('id')
    ).order_by('-count')[:10]  # Top 10 breeds

    if not breed_counts:
        return None

    df = pd.DataFrame(list(breed_counts))

    if df.empty:
        return None

    # Create figure
    fig, ax = plt.subplots(figsize=(8, 6))

    # Create horizontal bar chart
    colors = sns.color_palette('Reds_r', len(df))
    bars = ax.barh(df['breed'], df['count'], color=colors, edgecolor='white')

    ax.set_xlabel('Number of Fowl', fontsize=11)
    ax.set_title('Breed Distribution (Top 10)', fontsize=14, fontweight='bold')

    # Add value labels
    for bar in bars:
        width = bar.get_width()
        ax.annotate(f'{int(width)}',
                   xy=(width, bar.get_y() + bar.get_height() / 2),
                   xytext=(5, 0), textcoords='offset points',
                   ha='left', va='center', fontsize=10)

    plt.tight_layout()
    return fig_to_base64(fig)


def generate_bloodline_distribution_chart(fowl_queryset):
    """
    Generate a pie chart showing bloodline distribution across all fowl.
    """
    from apps.fowl.models import FowlBloodline

    # Get fowl IDs
    fowl_ids = fowl_queryset.values_list('id', flat=True)

    # Aggregate bloodlines
    bloodline_data = FowlBloodline.objects.filter(
        fowl_id__in=fowl_ids
    ).values(
        'bloodline__name'
    ).annotate(
        total_pct=Count('id')  # Count occurrences, not sum percentages
    ).order_by('-total_pct')[:8]  # Top 8

    if not bloodline_data:
        return None

    df = pd.DataFrame(list(bloodline_data))

    if df.empty:
        return None

    # Create figure
    fig, ax = plt.subplots(figsize=(7, 7))

    # Color palette
    colors = sns.color_palette('RdBu', len(df))

    wedges, texts, autotexts = ax.pie(
        df['total_pct'],
        labels=df['bloodline__name'],
        colors=colors,
        autopct='%1.1f%%',
        startangle=90,
        pctdistance=0.8
    )

    plt.setp(autotexts, size=10, weight='bold')
    plt.setp(texts, size=10)

    ax.set_title('Bloodline Distribution', fontsize=14, fontweight='bold', pad=20)

    return fig_to_base64(fig)


def generate_fowl_status_chart(fowl_queryset):
    """
    Generate a donut chart showing fowl status distribution.
    """
    status_counts = fowl_queryset.values('status').annotate(
        count=Count('id')
    ).order_by('-count')

    if not status_counts:
        return None

    df = pd.DataFrame(list(status_counts))

    if df.empty:
        return None

    # Define colors
    color_map = {
        'active': '#22C55E',     # Green-500
        'breeding': '#3B82F6',   # Blue-500
        'retired': '#F59E0B',    # Amber-500
        'deceased': '#6B7280',   # Gray-500
        'sold': '#8B5CF6',       # Violet-500
    }

    colors = [color_map.get(s, '#9CA3AF') for s in df['status']]

    # Create figure
    fig, ax = plt.subplots(figsize=(6, 6))

    wedges, texts, autotexts = ax.pie(
        df['count'],
        labels=[s.replace('_', ' ').title() for s in df['status']],
        colors=colors,
        autopct='%1.1f%%',
        startangle=90,
        pctdistance=0.75,
        wedgeprops=dict(width=0.5, edgecolor='white')
    )

    plt.setp(autotexts, size=11, weight='bold', color='white')
    plt.setp(texts, size=10)

    total = df['count'].sum()
    ax.text(0, 0, f'{total}\nFowl', ha='center', va='center',
            fontsize=16, fontweight='bold', color='#374151')

    ax.set_title('Fowl Status', fontsize=14, fontweight='bold', pad=20)

    return fig_to_base64(fig)


def generate_performance_trend_chart(fights_queryset, months=6):
    """
    Generate a line chart showing win rate trend over time.
    """
    end_date = timezone.now()
    start_date = end_date - timedelta(days=months * 30)

    monthly_data = fights_queryset.filter(
        scheduled_datetime__gte=start_date,
        status='completed'
    ).exclude(result='').annotate(
        month=TruncMonth('scheduled_datetime')
    ).values('month').annotate(
        total=Count('id'),
        wins=Count('id', filter=Q(result='win'))
    ).order_by('month')

    if not monthly_data:
        return None

    df = pd.DataFrame(list(monthly_data))

    if df.empty or len(df) < 2:
        return None

    df['win_rate'] = (df['wins'] / df['total'] * 100).round(1)
    df['month_label'] = df['month'].apply(lambda x: x.strftime('%b') if x else '')

    # Create figure
    fig, ax = plt.subplots(figsize=(8, 4))

    # Plot line
    ax.plot(df['month_label'], df['win_rate'], marker='o', color='#DC2626',
            linewidth=2, markersize=8, markerfacecolor='white', markeredgewidth=2)

    # Fill under line
    ax.fill_between(df['month_label'], df['win_rate'], alpha=0.3, color='#DC2626')

    ax.set_xlabel('Month', fontsize=11)
    ax.set_ylabel('Win Rate (%)', fontsize=11)
    ax.set_title('Win Rate Trend', fontsize=14, fontweight='bold')
    ax.set_ylim(0, 100)

    # Add percentage labels
    for i, (x, y) in enumerate(zip(df['month_label'], df['win_rate'])):
        ax.annotate(f'{y}%', (x, y), textcoords='offset points',
                   xytext=(0, 10), ha='center', fontsize=9)

    plt.tight_layout()
    return fig_to_base64(fig)


def get_dashboard_stats(user_profile):
    """
    Get summary statistics for the dashboard.
    Returns dict with key metrics.
    """
    from apps.fowl.models import Gamefowl
    from apps.fights.models import Fight

    is_admin = user_profile.is_admin

    # Get querysets based on role
    if is_admin:
        fowl_qs = Gamefowl.objects.all()
        fights_qs = Fight.objects.all()
    else:
        fowl_qs = Gamefowl.objects.filter(owner=user_profile)
        fowl_ids = fowl_qs.values_list('id', flat=True)
        fights_qs = Fight.objects.filter(fowl_id__in=fowl_ids)

    # Completed fights for calculations
    completed_fights = fights_qs.filter(status='completed')

    # Calculate stats
    total_fowl = fowl_qs.count()
    active_fowl = fowl_qs.filter(status='active').count()
    total_fights = fights_qs.count()
    completed_count = completed_fights.count()
    wins = completed_fights.filter(result='win').count()
    losses = completed_fights.filter(result='loss').count()

    win_rate = (wins / completed_count * 100) if completed_count > 0 else 0

    # Upcoming fights
    upcoming_fights = fights_qs.filter(
        status='scheduled',
        scheduled_datetime__gt=timezone.now()
    ).count()

    return {
        'total_fowl': total_fowl,
        'active_fowl': active_fowl,
        'total_fights': total_fights,
        'completed_fights': completed_count,
        'wins': wins,
        'losses': losses,
        'win_rate': round(win_rate, 1),
        'upcoming_fights': upcoming_fights,
    }
