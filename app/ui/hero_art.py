"""Original inline SVG used in the dashboard hero."""

from __future__ import annotations


def stacked_bars_svg() -> str:
    return """<svg viewBox="0 0 320 190" role="img" aria-label="Stylized stacked gold and silver bars" xmlns="http://www.w3.org/2000/svg">
    <defs><linearGradient id="gold" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#F7D66E"/><stop offset="1" stop-color="#B77A13"/></linearGradient><linearGradient id="silver" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#EAF2F4"/><stop offset="1" stop-color="#8A9BA9"/></linearGradient></defs>
    <ellipse cx="168" cy="158" rx="130" ry="18" fill="#020616" opacity=".4"/><path d="M70 117 145 83 255 103 180 141Z" fill="url(#silver)" stroke="#DCE8EC"/><path d="M70 117v18l110 40v-34Z" fill="#788B98"/><path d="M180 141v34l75-42v-30Z" fill="#9CAEB7"/>
    <path d="M45 91 119 57 225 77 151 116Z" fill="url(#gold)" stroke="#FFEBA0"/><path d="M45 91v18l106 39v-32Z" fill="#B77A13"/><path d="M151 116v32l74-42V77Z" fill="#915A0D"/><path d="M95 69 143 78 114 92 68 84Z" fill="#FFF2B1" opacity=".75"/>
    <path d="M122 53 172 30 247 44 197 70Z" fill="url(#gold)" stroke="#FFEBA0"/><path d="M122 53v15l75 27V70Z" fill="#B77A13"/><path d="M197 70v25l50-29V44Z" fill="#915A0D"/><text x="151" y="58" fill="#6B4207" font-size="10" font-family="sans-serif" font-weight="700">GOLDLENS</text></svg>"""
