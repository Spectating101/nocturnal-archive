// Debug button analysis to understand the clickability issue
const puppeteer = require('puppeteer');

async function debugButtons() {
  const browser = await puppeteer.launch({ 
    headless: true,  // Run invisibly in background
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080 });
  
  try {
    await page.goto('http://localhost:3000/research', { waitUntil: 'networkidle0' });
    
    const buttonAnalysis = await page.evaluate(() => {
      const buttons = document.querySelectorAll('button');
      const analysis = [];
      
      buttons.forEach((btn, index) => {
        analysis.push({
          index,
          text: btn.textContent?.trim() || 'No text',
          disabled: btn.disabled,
          type: btn.type,
          hasForm: !!btn.form,
          hasOnClick: !!btn.onclick,
          hasEventListener: btn.addEventListener ? 'Yes' : 'No',
          className: btn.className,
          id: btn.id,
          width: btn.offsetWidth,
          height: btn.offsetHeight,
          computedStyle: {
            cursor: getComputedStyle(btn).cursor,
            pointerEvents: getComputedStyle(btn).pointerEvents,
            opacity: getComputedStyle(btn).opacity
          }
        });
      });
      
      return analysis;
    });
    
    console.log('🔍 Button Analysis:');
    buttonAnalysis.forEach((btn, i) => {
      console.log(`\nButton ${i + 1}:`);
      console.log(`  Text: "${btn.text}"`);
      console.log(`  Disabled: ${btn.disabled}`);
      console.log(`  Type: ${btn.type}`);
      console.log(`  Has Form: ${btn.hasForm}`);
      console.log(`  Has onClick: ${btn.hasOnClick}`);
      console.log(`  Cursor: ${btn.computedStyle.cursor}`);
      console.log(`  Pointer Events: ${btn.computedStyle.pointerEvents}`);
      console.log(`  Opacity: ${btn.computedStyle.opacity}`);
      console.log(`  Size: ${btn.width}x${btn.height}`);
    });
    
  } finally {
    await browser.close();
  }
}

debugButtons().catch(console.error);
