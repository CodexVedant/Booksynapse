// ui.js — Tab switching, textarea autosize, validation, demo submit
document.addEventListener('DOMContentLoaded', function () {
    // Tabs
    const tabs = Array.from(document.querySelectorAll('.tab-card'));
    const panels = {
        similar: document.getElementById('panel-similar'),
        genre: document.getElementById('panel-genre'),
        mood: document.getElementById('panel-mood'),
        explore: document.getElementById('panel-explore')
    };

    function setActiveTab(tabName, clickedBtn) {
        tabs.forEach(t => {
            const isActive = t.dataset.tab === tabName;
            t.classList.toggle('active', isActive);
            t.setAttribute('aria-selected', isActive ? 'true' : 'false');
        });
        Object.keys(panels).forEach(k => {
            const el = panels[k];
            if (!el) return;
            if (k === tabName) {
                el.classList.remove('d-none');
                el.classList.add('active');
            } else {
                el.classList.add('d-none');
                el.classList.remove('active');
            }
        });
    }

    tabs.forEach(t => {
        t.addEventListener('click', () => setActiveTab(t.dataset.tab, t));
    });

    // Autosize textarea
    const textarea = document.getElementById('user-interests');
    if (textarea) {
        const autosize = el => {
            el.style.height = 'auto';
            el.style.height = (el.scrollHeight) + 'px';
        };
        autosize(textarea);
        textarea.addEventListener('input', () => autosize(textarea));
    }

    // CTA: Get Recommendations
    const getRecsBtn = document.getElementById('get-recs');
    const clearBtn = document.getElementById('clear-interests');
    const errEl = document.getElementById('interests-error');

    if (getRecsBtn) {
        getRecsBtn.addEventListener('click', async () => {
            const q = textarea ? textarea.value.trim() : '';
            if (!q) {
                // show error
                if (errEl) {
                    errEl.classList.remove('visually-hidden');
                }
                textarea && textarea.focus();
                return;
            } else {
                if (errEl) errEl.classList.add('visually-hidden');
            }

            const res = await fetch(`/api/recommendations?q=${encodeURIComponent(q)}`);
            const data = await res.json();
            renderResults('Similar Books', normalizeBooks(data));
        });
    }

    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            if (textarea) {
                textarea.value = '';
                textarea.style.height = 'auto';
            }
            if (errEl) errEl.classList.add('visually-hidden');
        });
    }

    // Genre submit
    const genreSubmit = document.getElementById('genre-submit');
    if (genreSubmit) {
        genreSubmit.addEventListener('click', async () => {
            const checks = Array.from(document.querySelectorAll('#panel-genre input[type="checkbox"]:checked'));
            const genres = checks.map(c => c.value.trim()).filter(Boolean);
            const qs = genres.length ? `?genres=${encodeURIComponent(genres.join(','))}` : '';
            const res = await fetch(`/api/search${qs}`);
            const data = await res.json();
            renderResults('Genre Picks', data);
        });
    }

    // Mood chips -> go to recommendations with query=mood
    const moodChips = Array.from(document.querySelectorAll('#panel-mood .mood-chip'));
    moodChips.forEach(btn => {
        btn.addEventListener('click', async () => {
            const mood = btn.textContent.trim();
            const res = await fetch(`/api/recommendations?q=${encodeURIComponent(mood)}`);
            const data = await res.json();
            renderResults('Mood Picks', normalizeBooks(data));
        });
    });

    // Mood input submit
    const moodInput = document.getElementById('mood-input');
    const moodSubmit = document.getElementById('mood-submit');
    if (moodSubmit) {
        moodSubmit.addEventListener('click', async () => {
            const mood = (moodInput && moodInput.value.trim()) || '';
            if (!mood) return;
            const res = await fetch(`/api/recommendations?q=${encodeURIComponent(mood)}`);
            const data = await res.json();
            renderResults('Mood Picks', normalizeBooks(data));
        });
    }

    // Explore: add button dynamically if not present
    const explorePanel = document.getElementById('panel-explore');
    const existingExploreBtn = document.getElementById('explore-btn');
    if (existingExploreBtn) {
        existingExploreBtn.addEventListener('click', async () => {
            const res = await fetch(`/api/explore`);
            const data = await res.json();
            renderResults('Explore New Territories', data);
        });
    } else if (explorePanel) {
        const btn = document.createElement('button');
        btn.id = 'explore-btn';
        btn.className = 'btn btn-primary btn-sm';
        btn.textContent = 'Surprise Me';
        explorePanel.appendChild(document.createElement('div')).appendChild(btn);
        btn.addEventListener('click', async () => {
            const res = await fetch(`/api/explore`);
            const data = await res.json();
            renderResults('Explore New Territories', data);
        });
    }

    function normalizeBooks(items) {
        return items.map(it => ({
            id: it.id,
            title: it.title,
            author: it.author,
            genres: it.genres,
            avg_rating: it.avg_rating || it.score || 0,
            ratings_count: it.ratings_count || 0
        }));
    }

    function renderResults(title, books) {
        const grid = document.getElementById('results-grid');
        const heading = document.getElementById('results-title');
        if (heading) heading.textContent = title;
        if (!grid) return;
        if (!books || !books.length) {
            grid.innerHTML = '<div class="col-12"><div class="alert alert-info">No results.</div></div>';
            return;
        }
        grid.innerHTML = books.map(b => {
            const g = b.genres ? (b.genres.length > 50 ? (b.genres.slice(0,50) + '...') : b.genres) : '';
            return `
            <div class="col-md-4 mb-4">
                <div class="card h-100 soft-card">
                    <div class="card-body">
                        <h5 class="card-title">${escapeHtml(b.title)}</h5>
                        <p class="card-text text-muted">by ${escapeHtml(b.author || '')}</p>
                        ${g ? `<p class="card-text"><small class="text-muted">${escapeHtml(g)}</small></p>` : ''}
                        <div class="mb-2">
                            <span class="badge bg-warning text-dark"><i class="fa-solid fa-star me-1"></i> ${Number(b.avg_rating).toFixed(1)}</span>
                            <span class="badge bg-secondary">${b.ratings_count} ratings</span>
                        </div>
                        <a href="/book/${b.id}" class="btn btn-sm btn-primary"><i class="fa-solid fa-circle-info me-1"></i> View Details</a>
                    </div>
                </div>
            </div>`;
        }).join('');
    }

    function escapeHtml(str) {
        return String(str).replace(/[&<>\"]/g, s => ({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;'}[s]));
    }

    // Keyboard navigation: left/right arrow to switch tabs
    document.addEventListener('keydown', (e) => {
        const activeIndex = tabs.findIndex(t => t.classList.contains('active'));
        if (activeIndex === -1) return;
        if (e.key === 'ArrowRight') {
            const next = tabs[(activeIndex + 1) % tabs.length];
            next && next.click();
        } else if (e.key === 'ArrowLeft') {
            const prev = tabs[(activeIndex - 1 + tabs.length) % tabs.length];
            prev && prev.click();
        }
    });
});
