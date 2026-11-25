// Desenha as setas dos slides a partir das caixas, para não precisar de coordenadas à mão.
//   <i class="seta" data-de="cliente.r" data-para="nginx.l"></i>
// Ponto = id.lado[.fração]: lado l|r|t|b (esquerda, direita, topo, base); fração ao longo do lado (padrão 0.5).
// Opcionais: data-rotulo="texto", data-rotulo-pos="acima|abaixo|direita|esquerda", data-cor="var(--java)",
// data-tracejada, data-dupla (ponta nos dois lados), data-reta (linha reta, alinhada à origem).
(function () {
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.id = 'setas';
  document.body.appendChild(svg);

  function ponto(spec) {
    const [id, lado, f = '0.5'] = spec.split('.').length > 2
      ? [spec.split('.')[0], spec.split('.')[1], spec.split('.').slice(2).join('.')]
      : spec.split('.');
    const el = document.getElementById(id);
    if (!el) throw new Error('caixa não encontrada: ' + id);
    const r = el.getBoundingClientRect();
    const k = Number(f);
    return {
      l: [r.left, r.top + r.height * k], r: [r.right, r.top + r.height * k],
      t: [r.left + r.width * k, r.top], b: [r.left + r.width * k, r.bottom],
    }[lado].concat(lado);
  }

  let n = 0;
  for (const s of document.querySelectorAll('.seta')) {
    const [x1, y1, l1] = ponto(s.dataset.de);
    let [x2, y2, l2] = ponto(s.dataset.para);
    const horiz = (l) => l === 'l' || l === 'r';
    // data-reta: a seta sai reta, alinhada ao ponto de partida (o destino só define o lado)
    if (s.hasAttribute('data-reta')) { if (horiz(l1)) y2 = y1; else x2 = x1; }
    let d, mx, my;
    if (horiz(l1) && horiz(l2)) {
      if (Math.abs(y1 - y2) < 2) { d = `M${x1} ${y1}H${x2}`; mx = (x1 + x2) / 2; my = y1; }
      else { const xm = (x1 + x2) / 2; d = `M${x1} ${y1}H${xm}V${y2}H${x2}`; mx = xm; my = (y1 + y2) / 2; }
    } else if (!horiz(l1) && !horiz(l2)) {
      if (Math.abs(x1 - x2) < 2) { d = `M${x1} ${y1}V${y2}`; mx = x1; my = (y1 + y2) / 2; }
      else { const ym = (y1 + y2) / 2; d = `M${x1} ${y1}V${ym}H${x2}V${y2}`; mx = (x1 + x2) / 2; my = ym; }
    } else if (horiz(l1)) { d = `M${x1} ${y1}H${x2}V${y2}`; mx = (x1 + x2) / 2; my = y1; }
    else { d = `M${x1} ${y1}V${y2}H${x2}`; mx = x1; my = (y1 + y2) / 2; }

    const cor = s.dataset.cor || 'var(--linha)';
    const id = 'ponta' + n++;
    svg.insertAdjacentHTML('beforeend',
      `<defs><marker id="${id}" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">` +
      `<path d="M0 0L10 5L0 10z" style="fill:${cor}"/></marker></defs>` +
      `<path d="${d}" fill="none" style="stroke:${cor}" stroke-width="4" stroke-linejoin="round"` +
      `${s.hasAttribute('data-tracejada') ? ' stroke-dasharray="14 10"' : ''} marker-end="url(#${id})"` +
      `${s.hasAttribute('data-dupla') ? ` marker-start="url(#${id})"` : ''}/>`);

    if (s.dataset.rotulo) {
      const r = document.createElement('div');
      r.className = 'rotulo';
      r.innerHTML = s.dataset.rotulo;
      if (s.dataset.cor) r.style.color = s.dataset.cor;
      document.body.appendChild(r);
      const pos = s.dataset.rotuloPos || 'acima';
      const t = { acima: 'translate(-50%, calc(-100% - 10px))', abaixo: 'translate(-50%, 10px)',
        direita: 'translate(14px, -50%)', esquerda: 'translate(calc(-100% - 14px), -50%)' }[pos];
      r.style.left = mx + 'px'; r.style.top = my + 'px'; r.style.transform = t;
    }
  }
  document.body.dataset.pronto = '1';
})();
