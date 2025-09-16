// Visual Feedback Loop for Nocturnal Archive
// This allows the AI to see and iterate on the frontend

const puppeteer = require('puppeteer');
const fs = require('fs');

async function captureAndAnalyze() {
  console.log('🔍 Starting visual analysis...');
  
  const browser = await puppeteer.launch({ 
    headless: false, // Show browser for debugging
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const page = await browser.newPage();
  
  // Set viewport for consistent screenshots
  await page.setViewport({ width: 1920, height: 1080 });
  
  try {
    // Navigate to the frontend
    console.log('📱 Navigating to frontend...');
    await page.goto('http://localhost:3000', { waitUntil: 'networkidle0' });
    
    // Take full page screenshot
    console.log('📸 Capturing screenshot...');
    await page.screenshot({ 
      path: 'frontend-current.png', 
      fullPage: true 
    });
    
    // Navigate to research page
    console.log('🔬 Testing research page...');
    await page.goto('http://localhost:3000/research', { waitUntil: 'networkidle0' });
    
    await page.screenshot({ 
      path: 'research-page.png', 
      fullPage: true 
    });
    
    // Test chat functionality
    console.log('💬 Testing chat interface...');
    const chatInput = await page.$('input[type="text"], textarea');
    if (chatInput) {
      await chatInput.type('Test research query');
      await page.screenshot({ 
        path: 'chat-input.png', 
        fullPage: true 
      });
    }
    
    // Analyze the page
    const analysis = await page.evaluate(() => {
      const issues = [];
      const score = { total: 0, passed: 0 };
      
      // Check for common UI issues
      const checks = {
        'No horizontal scroll': document.body.scrollWidth <= window.innerWidth,
        'All images loaded': Array.from(document.images).every(img => img.complete),
        'Buttons have proper size': Array.from(document.querySelectorAll('button')).every(
          btn => btn.offsetHeight >= 44 && btn.offsetWidth >= 44
        ),
        'No overlapping elements': (() => {
          const elements = document.querySelectorAll('button, a, input');
          for (let i = 0; i < elements.length; i++) {
            const rect1 = elements[i].getBoundingClientRect();
            for (let j = i + 1; j < elements.length; j++) {
              const rect2 = elements[j].getBoundingClientRect();
              if (!(rect1.right < rect2.left || 
                    rect1.left > rect2.right || 
                    rect1.bottom < rect2.top || 
                    rect1.top > rect2.bottom)) {
                return false;
              }
            }
          }
          return true;
        })(),
        'Responsive design': window.innerWidth < 768 ? 
          !!document.querySelector('[class*="mobile"], [class*="sm:"]') : true,
        'Chat interface present': !!document.querySelector('input[type="text"], textarea'),
        'Dark theme applied': document.body.style.backgroundColor.includes('dark') || 
          document.body.classList.contains('dark') ||
          getComputedStyle(document.body).backgroundColor.includes('rgb(15, 23, 42)')
      };
      
      // Calculate score
      Object.entries(checks).forEach(([check, passed]) => {
        score.total++;
        if (passed) score.passed++;
        else issues.push(check);
      });
      
      return {
        score: Math.round((score.passed / score.total) * 100),
        issues,
        checks,
        pageInfo: {
          title: document.title,
          url: window.location.href,
          viewport: { width: window.innerWidth, height: window.innerHeight }
        }
      };
    });
    
    console.log('\n📊 VISUAL ANALYSIS RESULTS:');
    console.log(`Score: ${analysis.score}/100`);
    console.log(`Page: ${analysis.pageInfo.title}`);
    console.log(`URL: ${analysis.pageInfo.url}`);
    
    if (analysis.issues.length > 0) {
      console.log('\n❌ Issues found:');
      analysis.issues.forEach(issue => console.log(`  - ${issue}`));
    } else {
      console.log('\n✅ No issues found!');
    }
    
    // Save analysis results
    fs.writeFileSync('visual-analysis.json', JSON.stringify(analysis, null, 2));
    
    console.log('\n📁 Files created:');
    console.log('  - frontend-current.png (main page)');
    console.log('  - research-page.png (research interface)');
    console.log('  - chat-input.png (chat interface)');
    console.log('  - visual-analysis.json (detailed results)');
    
  } catch (error) {
    console.error('❌ Error during analysis:', error.message);
  } finally {
    await browser.close();
  }
}

// Run the analysis
captureAndAnalyze().then(() => {
  console.log('\n🎉 Visual analysis complete!');
}).catch(console.error);

