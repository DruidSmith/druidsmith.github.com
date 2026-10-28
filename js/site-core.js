/**
 * /js/site-core.js
 * Unified Navigation, Webhook Subscription Modal/Toast & GA4/Clarity Journey Funnel Engine
 * for https://davidgsmith.net
 */
(function () {
    if (window.DGSAnalytics && window.DGSAnalytics._initialized) return;

    const WEBHOOK_URL = 'https://webhook.davidgsmith.net/webhook/subscriber-capture';
    const STORAGE_KEY = 'dgs_user_journey_v1';

    function detectReferrerSource(ref) {
        if (!ref) return 'direct';
        const r = ref.toLowerCase();
        if (r.includes('linkedin.com')) return 'linkedin';
        if (r.includes('reddit.com')) return 'reddit';
        if (r.includes('bsky.app')) return 'bluesky';
        if (r.includes('mastodon')) return 'mastodon';
        if (r.includes('t.co') || r.includes('twitter.com') || r.includes('x.com')) return 'twitter';
        if (r.includes('google.')) return 'google';
        if (r.includes('bing.')) return 'bing';
        if (r.includes('goodreads.com')) return 'goodreads';
        if (r.includes('bookbub.com')) return 'bookbub';
        if (r.includes('quora.com')) return 'quora';
        return 'referral';
    }

    function getJourneyState() {
        try {
            const raw = sessionStorage.getItem(STORAGE_KEY);
            if (raw) return JSON.parse(raw);
        } catch (e) {}
        const params = new URLSearchParams(window.location.search);
        return {
            landing_page: window.location.pathname || '/',
            initial_referrer: document.referrer || 'direct',
            utm_source: params.get('utm_source') || detectReferrerSource(document.referrer),
            utm_medium: params.get('utm_medium') || 'organic_or_direct',
            path_sequence: [],
            prior_actions: []
        };
    }

    function saveJourneyState(state) {
        try {
            sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state));
        } catch (e) {}
    }

    function recordAction(actionStr) {
        const state = getJourneyState();
        state.prior_actions = state.prior_actions || [];
        state.prior_actions.push(actionStr);
        if (state.prior_actions.length > 15) state.prior_actions.shift();
        saveJourneyState(state);
    }

    function ensureFeedbackContainers() {
        if (!document.getElementById('sub-toast')) {
            const toastHtml = `
            <div id="sub-toast" role="status" aria-live="polite" class="fixed bottom-24 right-6 z-50 hidden max-w-sm bg-slate-900 border border-slate-700 text-white px-5 py-4 rounded-xl shadow-2xl flex items-start gap-3 transition-all duration-300">
                <span id="sub-toast-icon" class="mt-0.5 text-emerald-400 shrink-0"></span>
                <div class="text-xs sm:text-sm flex-1">
                    <p id="sub-toast-title" class="font-semibold text-white">Subscription Update</p>
                    <p id="sub-toast-msg" class="text-slate-300 mt-0.5"></p>
                </div>
                <button type="button" onclick="closeSubFeedback()" class="text-slate-400 hover:text-white p-1" aria-label="Close notification">&times;</button>
            </div>`;
            document.body.insertAdjacentHTML('beforeend', toastHtml);
        }

        if (!document.getElementById('sub-modal')) {
            const modalHtml = `
            <div id="sub-modal" role="dialog" aria-modal="true" aria-labelledby="sub-modal-title" class="fixed inset-0 z-50 hidden flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
                <div class="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 sm:p-8 shadow-2xl text-center space-y-4 relative">
                    <button type="button" onclick="closeSubFeedback()" class="absolute top-4 right-4 text-slate-400 hover:text-white p-1" aria-label="Dismiss modal">
                        <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
                    </button>
                    <div id="sub-modal-badge" class="w-12 h-12 rounded-full mx-auto flex items-center justify-center bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"></div>
                    <h3 id="sub-modal-title" class="text-xl font-serif font-semibold text-white"></h3>
                    <p id="sub-modal-message" class="text-sm text-slate-300 leading-relaxed"></p>
                    <p class="text-xs text-amber-400/90 font-medium">The Spatial, Data &amp; AI Architecture Digest is coming soon — you are locked in for the inaugural issue.</p>
                    <div class="pt-2">
                        <button type="button" onclick="closeSubFeedback()" class="w-full py-2.5 px-5 bg-brand-accent hover:bg-amber-700 text-white font-semibold rounded-lg text-xs sm:text-sm transition-colors">
                            Got It
                        </button>
                    </div>
                </div>
            </div>`;
            document.body.insertAdjacentHTML('beforeend', modalHtml);
        }
    }

    window.showSubFeedback = function (isSuccess, title, message) {
        ensureFeedbackContainers();
        const toast = document.getElementById('sub-toast');
        const toastTitle = document.getElementById('sub-toast-title');
        const toastMsg = document.getElementById('sub-toast-msg');
        const toastIcon = document.getElementById('sub-toast-icon');

        const modal = document.getElementById('sub-modal');
        const modalTitle = document.getElementById('sub-modal-title');
        const modalMsg = document.getElementById('sub-modal-message');
        const modalBadge = document.getElementById('sub-modal-badge');

        const checkSvg = '<svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>';
        const errSvg = '<svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>';

        if (toast && toastTitle && toastMsg) {
            toastTitle.textContent = title;
            toastMsg.textContent = message;
            toastIcon.innerHTML = isSuccess ? checkSvg : errSvg;
            toastIcon.className = isSuccess ? 'mt-0.5 text-emerald-400 shrink-0' : 'mt-0.5 text-rose-400 shrink-0';
            toast.classList.remove('hidden');
        }

        if (modal && modalTitle && modalMsg) {
            modalTitle.textContent = title;
            modalMsg.textContent = message;
            modalBadge.innerHTML = isSuccess ? checkSvg : errSvg;
            modalBadge.className = isSuccess
                ? 'w-12 h-12 rounded-full mx-auto flex items-center justify-center bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                : 'w-12 h-12 rounded-full mx-auto flex items-center justify-center bg-rose-500/20 text-rose-400 border border-rose-500/30';
            modal.classList.remove('hidden');
        }
    };

    window.closeSubFeedback = function () {
        const toast = document.getElementById('sub-toast');
        const modal = document.getElementById('sub-modal');
        if (toast) toast.classList.add('hidden');
        if (modal) modal.classList.add('hidden');
    };

    function recordPageView() {
        const state = getJourneyState();
        const currentPath = window.location.pathname || '/';
        const previousPage = state.path_sequence.length > 0 ? state.path_sequence[state.path_sequence.length - 1] : 'entry';

        if (previousPage !== currentPath) {
            state.path_sequence.push(currentPath);
            if (state.path_sequence.length > 15) state.path_sequence.shift();
            saveJourneyState(state);
        }

        const journeyString = state.path_sequence.join(' -> ');
        const priorActionsStr = (state.prior_actions || []).slice(-8).join(' | ') || 'none';

        if (typeof window.clarity === 'function') {
            window.clarity('set', 'landing_page', state.landing_page);
            window.clarity('set', 'initial_source', state.utm_source);
            window.clarity('set', 'journey_path', journeyString);
        }

        if (currentPath.includes('critical-thinking') || currentPath.includes('books')) {
            if (typeof gtag === 'function') {
                gtag('event', 'book_page_reached', {
                    page_path: currentPath,
                    previous_internal_page: previousPage,
                    landing_page: state.landing_page,
                    initial_referrer: state.initial_referrer,
                    traffic_source: state.utm_source,
                    journey_path: journeyString,
                    prior_actions: priorActionsStr,
                    journey_steps: state.path_sequence.length
                });
            }
            if (typeof window.clarity === 'function') {
                window.clarity('set', 'funnel_stage', 'viewed_book_page');
            }
        }
    }

    function trackOutboundBookAction(event, linkEl, actionCategory, platformName, bookFormat) {
        if (!linkEl) return;
        const state = getJourneyState();
        const journeyString = state.path_sequence.join(' -> ');
        const previousPage = state.path_sequence.length > 1 ? state.path_sequence[state.path_sequence.length - 2] : state.initial_referrer;
        let targetUrl = linkEl.getAttribute('href') || '';

        if (targetUrl && targetUrl.includes('amazon.com')) {
            try {
                const url = new URL(targetUrl);
                url.searchParams.set('utm_source', state.utm_source || 'website');
                url.searchParams.set('utm_medium', state.utm_medium || 'author_site');
                url.searchParams.set('utm_campaign', 'critical_thinking_book');
                url.searchParams.set('utm_content', bookFormat || actionCategory);
                targetUrl = url.toString();
                linkEl.setAttribute('href', targetUrl);
            } catch (e) {}
        }

        recordAction(actionCategory + ':' + platformName);

        const payload = {
            event_category: actionCategory,
            platform: platformName,
            book_format: bookFormat || 'n/a',
            source_page: window.location.pathname,
            previous_page: previousPage,
            landing_page: state.landing_page,
            initial_referrer: state.initial_referrer,
            journey_path: journeyString,
            prior_actions: (state.prior_actions || []).slice(-8).join(' | '),
            journey_steps: state.path_sequence.length,
            outbound_url: targetUrl,
            transport_type: 'beacon'
        };

        if (typeof gtag === 'function') {
            gtag('event', actionCategory, payload);
        }
        if (typeof window.clarity === 'function') {
            window.clarity('set', 'conversion_action', actionCategory + ':' + platformName);
            window.clarity('event', actionCategory);
        }
    }

    async function handleSubscriptionSubmit(event) {
        event.preventDefault();
        const form = event.currentTarget;
        const emailInput = form.querySelector('input[name="email"]');
        const tagInput = form.querySelector('input[name="tag"]');
        const submitBtn = form.querySelector('button[type="submit"], [data-submit-btn]');
        const sourcePage = form.getAttribute('data-source-page') || window.location.pathname;

        const email = emailInput ? emailInput.value.trim() : '';
        const tag = tagInput ? tagInput.value : 'site-digest';
        if (!email) return;

        const state = getJourneyState();
        const journeyString = state.path_sequence.join(' -> ');
        const previousPage = state.path_sequence.length > 1 ? state.path_sequence[state.path_sequence.length - 2] : state.initial_referrer;

        const baseTelemetry = {
            source_page: sourcePage,
            subscription_tag: tag,
            previous_page: previousPage,
            landing_page: state.landing_page,
            initial_referrer: state.initial_referrer,
            journey_path: journeyString,
            prior_actions: (state.prior_actions || []).slice(-8).join(' | ') || 'none',
            journey_steps: state.path_sequence.length
        };

        if (typeof gtag === 'function') {
            gtag('event', 'newsletter_subscribe_attempt', baseTelemetry);
        }

        const originalBtnHtml = submitBtn ? submitBtn.innerHTML : '';
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span>Submitting...</span>';
        }

        try {
            const response = await fetch(WEBHOOK_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({
                    email: email,
                    tag: tag,
                    source_page: window.location.pathname,
                    journey_path: journeyString,
                    referrer: state.initial_referrer
                })
            });

            let data = null;
            try {
                data = await response.json();
            } catch (_) {
                data = null;
            }

            if (response.ok && data && data.success === true) {
                const msg = data.message || 'Thank you for subscribing!';
                window.showSubFeedback(true, 'Subscription Confirmed', msg);
                form.reset();

                if (typeof gtag === 'function') {
                    gtag('event', 'generate_lead', Object.assign({}, baseTelemetry, {
                        event_category: 'Newsletter',
                        event_label: tag,
                        webhook_message: msg
                    }));
                    gtag('event', 'newsletter_subscribe_success', Object.assign({}, baseTelemetry, {
                        webhook_message: msg
                    }));
                }
                if (typeof window.clarity === 'function') {
                    window.clarity('set', 'subscribed', 'true');
                    window.clarity('set', 'subscription_journey', journeyString);
                    window.clarity('event', 'newsletter_subscribe_success');
                }
            } else {
                throw new Error((data && data.message) ? data.message : 'Unexpected response from subscription server.');
            }
        } catch (err) {
            window.showSubFeedback(false, 'Subscription Error', 'An error occurred while processing your subscription request. Please try again in a moment.');
            if (typeof gtag === 'function') {
                gtag('event', 'newsletter_subscribe_error', Object.assign({}, baseTelemetry, {
                    error_message: err.message || 'fetch_error'
                }));
            }
            if (typeof window.clarity === 'function') {
                window.clarity('event', 'newsletter_subscribe_error');
            }
        } finally {
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalBtnHtml;
            }
        }
    }

    function bindGlobalClickDelegation() {
        document.addEventListener('click', function (e) {
            const link = e.target.closest('a');
            if (!link) return;

            const href = link.getAttribute('href') || '';
            const lowerHref = href.toLowerCase();
            const linkText = (link.textContent || '').trim().slice(0, 60);

            if (link.dataset.priorAction) {
                recordAction(link.dataset.priorAction);
            } else if (href.includes('/thoughts-')) {
                recordAction('tag_filter:' + linkText);
            } else if (href.includes('/thoughts/')) {
                recordAction('read_post:' + href.split('/').pop().replace('.html', ''));
            }

            // Internal navigation to Book pages
            if (href.includes('critical-thinking.html') || href.includes('books.html')) {
                const state = getJourneyState();
                const sourceLoc = link.dataset.bookFunnel || linkText || 'inline_link';
                recordAction('to_book_via:' + sourceLoc + '@' + window.location.pathname);
                if (typeof gtag === 'function') {
                    gtag('event', 'book_interest_click', {
                        event_category: 'Book Funnel',
                        target_page: href,
                        source_page: window.location.pathname,
                        link_location: sourceLoc,
                        landing_page: state.landing_page,
                        journey_path: state.path_sequence.join(' -> '),
                        prior_actions: (state.prior_actions || []).slice(-8).join(' | ')
                    });
                }
            }

            // Auto-track outbound review sites & Amazon links if not already handled by inline onclick
            if (!link.getAttribute('onclick')) {
                if (lowerHref.includes('amazon.com/dp/b0hh3cyk79') || lowerHref.includes('amazon.com/critical-thinking') || lowerHref.includes('b0hh8dv2k4')) {
                    const isSample = lowerHref.includes('format=4') || linkText.toLowerCase().includes('sample');
                    const isKindle = lowerHref.includes('b0hh8dv2k4') || linkText.toLowerCase().includes('kindle');
                    trackOutboundBookAction(e, link, isSample ? 'book_sample_click' : 'book_purchase_click', 'Amazon', isSample ? 'sample' : (isKindle ? 'kindle' : 'paperback'));
                } else if (lowerHref.includes('goodreads.com')) {
                    trackOutboundBookAction(e, link, lowerHref.includes('/book/') ? 'book_review_site_click' : 'author_profile_click', 'Goodreads', 'goodreads');
                } else if (lowerHref.includes('bookbub.com')) {
                    trackOutboundBookAction(e, link, lowerHref.includes('/books/') ? 'book_review_site_click' : 'author_profile_click', 'BookBub', 'bookbub');
                } else if (lowerHref.includes('librarything.com')) {
                    trackOutboundBookAction(e, link, lowerHref.includes('/work/') ? 'book_review_site_click' : 'author_profile_click', 'LibraryThing', 'librarything');
                } else if (lowerHref.includes('thestorygraph.com')) {
                    trackOutboundBookAction(e, link, 'author_profile_click', 'StoryGraph', 'storygraph');
                } else if (lowerHref.includes('bookwyrm.social')) {
                    trackOutboundBookAction(e, link, lowerHref.includes('/book/') ? 'book_review_site_click' : 'author_profile_click', 'BookWyrm', 'bookwyrm');
                }
            }
        });
    }

    function initDOM() {
        const yearEl = document.getElementById('year');
        if (yearEl) yearEl.textContent = new Date().getFullYear();

        const btn = document.getElementById('mobile-menu-btn');
        const menu = document.getElementById('mobile-menu');
        const mobileLinks = document.querySelectorAll('.mobile-link');

        if (btn && menu && !btn.dataset.navBound) {
            btn.dataset.navBound = 'true';
            btn.addEventListener('click', () => {
                const isHidden = menu.classList.toggle('hidden');
                btn.setAttribute('aria-expanded', String(!isHidden));
            });
            mobileLinks.forEach(link => link.addEventListener('click', () => {
                menu.classList.add('hidden');
                btn.setAttribute('aria-expanded', 'false');
            }));
        }

        const closeStickyBtn = document.getElementById('close-sticky-banner');
        if (closeStickyBtn && !closeStickyBtn.dataset.bound) {
            closeStickyBtn.dataset.bound = 'true';
            closeStickyBtn.addEventListener('click', function () {
                const banner = document.getElementById('sticky-relief-banner');
                if (banner) banner.style.display = 'none';
            });
        }

        ensureFeedbackContainers();
        recordPageView();
        bindGlobalClickDelegation();

        // Bind all newsletter forms (including legacy buttondown forms if any exist)
        const forms = document.querySelectorAll('form[data-newsletter-form], form[action*="subscriber-capture"], form[action*="buttondown.com"]');
        forms.forEach(form => {
            if (form.dataset.webhookBound) return;
            form.dataset.webhookBound = 'true';
            form.setAttribute('action', WEBHOOK_URL);
            form.removeAttribute('target');
            form.removeAttribute('onsubmit');
            form.addEventListener('submit', handleSubscriptionSubmit);
        });
    }

    window.DGSAnalytics = {
        _initialized: true,
        init: initDOM,
        trackBook: trackOutboundBookAction
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initDOM);
    } else {
        initDOM();
    }
})();