// Enhanced Visual Analysis with AI Integration
const puppeteer = require('puppeteer');
const fs = require('fs');

async function enhancedVisualAnalysis() {
  console.log('🔍 Starting Enhanced Visual Analysis...');
  
  const browser = await puppeteer.launch({ 
    headless: true,  // Run invisibly in background
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080 });
  
  try {
    // Test multiple pages
    const pages = [
      { name: 'Home', url: 'http://localhost:3000' },
      { name: 'Research', url: 'http://localhost:3000/research' }
    ];
    
    const results = {};
    
    for (const pageInfo of pages) {
      console.log(`\n📱 Testing ${pageInfo.name} page...`);
      await page.goto(pageInfo.url, { waitUntil: 'networkidle0' });
      
      // Take screenshot
      const screenshotPath = `${pageInfo.name.toLowerCase()}-analysis.png`;
      await page.screenshot({ path: screenshotPath, fullPage: true });
      
      // Analyze page
      const analysis = await page.evaluate(() => {
        const elements = {
          buttons: document.querySelectorAll('button'),
          inputs: document.querySelectorAll('input, textarea'),
          links: document.querySelectorAll('a'),
          images: document.querySelectorAll('img'),
          forms: document.querySelectorAll('form')
        };
        
        const checks = {
          // Visual checks
          noHorizontalScroll: document.body.scrollWidth <= window.innerWidth,
          allImagesLoaded: Array.from(elements.images).every(img => img.complete),
          buttonsLargeEnough: Array.from(elements.buttons).every(
            btn => btn.offsetHeight >= 44 && btn.offsetWidth >= 44
          ),
          
          // Functional checks
          chatInterfacePresent: !!document.querySelector('input[type="text"], textarea'),
          buttonsClickable: Array.from(elements.buttons).every(btn => {
            // Allow disabled state for submit buttons when form is empty (good UX)
            if (btn.type === 'submit' && btn.form) {
              const inputs = btn.form.querySelectorAll('input, textarea');
              const hasValue = Array.from(inputs).some(input => input.value.trim());
              // If form has no value, disabled state is acceptable
              if (!hasValue) return true;
            }
            return !btn.disabled;
          }),
          formsHaveValidation: Array.from(elements.forms).every(
            form => form.querySelectorAll('[required]').length > 0
          ),
          
          // Layout checks
          noOverlapping: (() => {
            const interactiveElements = document.querySelectorAll('button, a, input');
            for (let i = 0; i < interactiveElements.length; i++) {
              const rect1 = interactiveElements[i].getBoundingClientRect();
              for (let j = i + 1; j < interactiveElements.length; j++) {
                const rect2 = interactiveElements[j].getBoundingClientRect();
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
          
          // Theme checks
          darkThemeApplied: (() => {
            const body = document.body;
            const computedStyle = getComputedStyle(body);
            const bgColor = computedStyle.backgroundColor;
            return bgColor.includes('rgb(15, 23, 42)') || 
                   bgColor.includes('rgb(30, 41, 59)') ||
                   body.classList.contains('dark') ||
                   body.getAttribute('data-theme') === 'dark';
          })(),
          
          // Responsive design
          mobileReady: window.innerWidth < 768 ? 
            !!document.querySelector('[class*="mobile"], [class*="sm:"]') : true,
        };
        
        // Get element details
        const elementDetails = {
          buttonCount: elements.buttons.length,
          inputCount: elements.inputs.length,
          linkCount: elements.links.length,
          imageCount: elements.images.length,
          formCount: elements.forms.length,
          buttonSizes: Array.from(elements.buttons).map(btn => ({
            width: btn.offsetWidth,
            height: btn.offsetHeight,
            text: btn.textContent?.trim() || 'No text'
          }))
        };
        
        const score = Math.round((Object.values(checks).filter(Boolean).length / Object.keys(checks).length) * 100);
        const issues = Object.entries(checks).filter(([_, passed]) => !passed).map(([test]) => test);
        
        return {
          score,
          issues,
          checks,
          elementDetails,
          pageInfo: {
            title: document.title,
            url: window.location.href,
            viewport: { width: window.innerWidth, height: window.innerHeight },
            scrollDimensions: { width: document.body.scrollWidth, height: document.body.scrollHeight }
          }
        };
      });
      
      results[pageInfo.name] = analysis;
      console.log(`✅ ${pageInfo.name} Score: ${analysis.score}/100`);
      
      if (analysis.issues.length > 0) {
        console.log(`   Issues: ${analysis.issues.join(', ')}`);
      }
    }
    
    // Test chat functionality
    console.log('\n💬 Testing chat functionality...');
    await page.goto('http://localhost:3000/research', { waitUntil: 'networkidle0' });
    
    // Try to find and interact with chat input
    const chatInput = await page.$('input[type="text"], textarea');
    if (chatInput) {
      await chatInput.type('Test research query for visual analysis');
      await page.screenshot({ path: 'chat-interaction.png', fullPage: true });
      console.log('✅ Chat input found and tested');
    } else {
      console.log('❌ No chat input found');
    }
    
    // Save comprehensive results
    const comprehensiveResults = {
      timestamp: new Date().toISOString(),
      overallScore: Math.round(Object.values(results).reduce((sum, r) => sum + r.score, 0) / Object.keys(results).length),
      pages: results,
      recommendations: generateRecommendations(results)
    };
    
    fs.writeFileSync('comprehensive-visual-analysis.json', JSON.stringify(comprehensiveResults, null, 2));
    
    console.log('\n📊 COMPREHENSIVE ANALYSIS RESULTS:');
    console.log(`Overall Score: ${comprehensiveResults.overallScore}/100`);
    console.log('\n📁 Files created:');
    console.log('  - home-analysis.png');
    console.log('  - research-analysis.png');
    console.log('  - chat-interaction.png');
    console.log('  - comprehensive-visual-analysis.json');
    
    // Display recommendations
    if (comprehensiveResults.recommendations.length > 0) {
      console.log('\n💡 RECOMMENDATIONS:');
      comprehensiveResults.recommendations.forEach((rec, i) => {
        console.log(`  ${i + 1}. ${rec}`);
      });
    }
    
  } catch (error) {
    console.error('❌ Error during analysis:', error.message);
  } finally {
    await browser.close();
  }
}

function generateRecommendations(results) {
  const recommendations = [];
  
  Object.entries(results).forEach(([pageName, analysis]) => {
    if (analysis.issues.includes('Dark theme applied')) {
      recommendations.push(`Fix dark theme detection on ${pageName} page`);
    }
    if (analysis.issues.includes('Buttons have proper size')) {
      recommendations.push(`Increase button sizes on ${pageName} page for better touch targets`);
    }
    if (analysis.issues.includes('No overlapping elements')) {
      recommendations.push(`Fix overlapping elements on ${pageName} page`);
    }
    if (analysis.issues.includes('Chat interface present')) {
      recommendations.push(`Ensure chat interface is properly implemented on ${pageName} page`);
    }
  });
  
  return [...new Set(recommendations)]; // Remove duplicates
}

// Run the enhanced analysis
enhancedVisualAnalysis().then(() => {
  console.log('\n🎉 Enhanced visual analysis complete!');
}).catch(console.error);
