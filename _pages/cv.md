---
layout: page
permalink: /cv/
title: cv
nav: true
nav_order: 5
---

{% assign cv_pdf = '/assets/pdf/YifengLiu_CV.pdf' | relative_url %}

<p><a href="{{ cv_pdf }}" class="btn btn-sm z-depth-0" role="button" target="_blank" rel="noopener noreferrer" style="color: var(--global-text-color); border: 1px solid var(--global-text-color); padding: 0.25rem 1rem; margin-left: 0;">Download CV (PDF)</a></p>

<object data="{{ cv_pdf }}#view=FitH" type="application/pdf" aria-label="Yifeng Liu CV" style="display: block; width: 100%; aspect-ratio: 8.5 / 11.6; border: 1px solid var(--global-divider-color);">
  <p>Your browser cannot preview the PDF here. <a href="{{ cv_pdf }}" target="_blank" rel="noopener noreferrer">Open the CV</a>.</p>
</object>
