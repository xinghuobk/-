(function() {
  var style = getComputedStyle(document.documentElement);
  var accent = style.getPropertyValue('--accent').trim();
  var accent2 = style.getPropertyValue('--accent2').trim();
  var ink = style.getPropertyValue('--ink').trim();
  var muted = style.getPropertyValue('--muted').trim();
  var rule = style.getPropertyValue('--rule').trim();
  var bg2 = style.getPropertyValue('--bg2').trim();
  var bg3 = style.getPropertyValue('--bg3').trim();
  var green = style.getPropertyValue('--green').trim();
  var orange = style.getPropertyValue('--orange').trim();

  // --- Chart 1: Winner Distribution (Pie) ---
  var chart1 = echarts.init(document.getElementById('chart-winner'), null, { renderer: 'svg' });
  chart1.setOption({
    animation: false,
    tooltip: { trigger: 'item', appendToBody: true, formatter: '{b}: {c} ({d}%)' },
    legend: { bottom: 10, textStyle: { color: muted, fontSize: 12 }, itemWidth: 12, itemHeight: 12 },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['50%', '45%'],
      avoidLabelOverlap: true,
      itemStyle: { borderRadius: 6, borderColor: bg2, borderWidth: 2 },
      label: { color: ink, fontSize: 12, formatter: '{b}\n{c} 轮' },
      labelLine: { lineStyle: { color: rule } },
      data: [
        { value: 333, name: 'AI 是否导致失业', itemStyle: { color: accent } },
        { value: 334, name: '城市禁止燃油车', itemStyle: { color: accent2 } },
        { value: 333, name: '远程办公主流化', itemStyle: { color: green } }
      ]
    }]
  });
  window.addEventListener('resize', function() { chart1.resize(); });

  // --- Chart 2: Score Trend (Line) ---
  var chart2 = echarts.init(document.getElementById('chart-trend'), null, { renderer: 'svg' });
  var xLabels = ['1-100', '101-200', '201-300', '301-400', '401-500', '501-600', '601-700', '701-800', '801-900', '901-1000'];
  var proAvg = [55.53, 55.53, 55.53, 55.53, 55.53, 55.53, 55.53, 55.53, 55.53, 55.53];
  var conAvg = [55.13, 55.13, 55.13, 55.13, 55.13, 55.13, 55.13, 55.13, 55.13, 55.13];
  chart2.setOption({
    animation: false,
    tooltip: { trigger: 'axis', appendToBody: true },
    legend: { bottom: 10, textStyle: { color: muted, fontSize: 12 }, itemWidth: 16, itemHeight: 3 },
    grid: { left: 50, right: 20, top: 20, bottom: 50 },
    xAxis: { type: 'category', data: xLabels, axisLine: { lineStyle: { color: rule } }, axisLabel: { color: muted, fontSize: 11, rotate: 30 } },
    yAxis: { type: 'value', min: 52, max: 58, axisLine: { lineStyle: { color: rule } }, splitLine: { lineStyle: { color: rule, type: 'dashed' } }, axisLabel: { color: muted, fontSize: 11 } },
    series: [
      { name: '正方 (Pro)', type: 'line', data: proAvg, smooth: true, lineStyle: { color: accent, width: 2 }, itemStyle: { color: accent }, symbol: 'circle', symbolSize: 6, areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: accent + '30' }, { offset: 1, color: accent + '05' }] } } },
      { name: '反方 (Con)', type: 'line', data: conAvg, smooth: true, lineStyle: { color: accent2, width: 2 }, itemStyle: { color: accent2 }, symbol: 'circle', symbolSize: 6, areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: accent2 + '30' }, { offset: 1, color: accent2 + '05' }] } } }
    ]
  });
  window.addEventListener('resize', function() { chart2.resize(); });

  // --- Chart 3: Performance Trend (Bar) ---
  var chart3 = echarts.init(document.getElementById('chart-perf'), null, { renderer: 'svg' });
  var perfData = [975, 893, 870, 977, 986, 1015, 1015, 999, 966, 1082];
  chart3.setOption({
    animation: false,
    tooltip: { trigger: 'axis', appendToBody: true, formatter: function(p) { return p[0].name + '<br/>耗时: ' + p[0].value + ' ms'; } },
    grid: { left: 60, right: 20, top: 20, bottom: 50 },
    xAxis: { type: 'category', data: xLabels, axisLine: { lineStyle: { color: rule } }, axisLabel: { color: muted, fontSize: 11, rotate: 30 } },
    yAxis: { type: 'value', name: 'ms', nameTextStyle: { color: muted }, axisLine: { lineStyle: { color: rule } }, splitLine: { lineStyle: { color: rule, type: 'dashed' } }, axisLabel: { color: muted, fontSize: 11 } },
    series: [{
      type: 'bar',
      data: perfData.map(function(v, i) {
        return { value: v, itemStyle: { color: v > 1000 ? orange + 'cc' : accent + '99', borderRadius: [3, 3, 0, 0] } };
      }),
      barWidth: '50%'
    }]
  });
  window.addEventListener('resize', function() { chart3.resize(); });

  // --- Chart 4: Resource Consumption (Multi-axis) ---
  var chart4 = echarts.init(document.getElementById('chart-resource'), null, { renderer: 'svg' });
  var diskData = [63, 125, 187, 249, 312, 374, 436, 498, 561, 623];
  var memData = [41, 42, 43, 44, 44, 44, 44, 44, 44, 45];
  chart4.setOption({
    animation: false,
    tooltip: { trigger: 'axis', appendToBody: true },
    legend: { bottom: 10, textStyle: { color: muted, fontSize: 12 }, itemWidth: 16, itemHeight: 3 },
    grid: { left: 60, right: 60, top: 20, bottom: 50 },
    xAxis: { type: 'category', data: xLabels, axisLine: { lineStyle: { color: rule } }, axisLabel: { color: muted, fontSize: 11, rotate: 30 } },
    yAxis: [
      { type: 'value', name: '磁盘 (KB)', nameTextStyle: { color: muted }, axisLine: { lineStyle: { color: rule } }, splitLine: { lineStyle: { color: rule, type: 'dashed' } }, axisLabel: { color: muted, fontSize: 11 } },
      { type: 'value', name: '内存 (MB)', nameTextStyle: { color: muted }, axisLine: { lineStyle: { color: rule } }, splitLine: { show: false }, axisLabel: { color: muted, fontSize: 11 }, min: 38, max: 50 }
    ],
    series: [
      { name: '磁盘 (KB)', type: 'bar', yAxisIndex: 0, data: diskData, itemStyle: { color: accent + '99', borderRadius: [3, 3, 0, 0] }, barWidth: '40%' },
      { name: '内存 (MB)', type: 'line', yAxisIndex: 1, data: memData, smooth: true, lineStyle: { color: orange, width: 2 }, itemStyle: { color: orange }, symbol: 'circle', symbolSize: 6 }
    ]
  });
  window.addEventListener('resize', function() { chart4.resize(); });
})();
