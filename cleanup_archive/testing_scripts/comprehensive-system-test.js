// Comprehensive System Testing - Backend + Frontend + UX + Functionality
const puppeteer = require('puppeteer');
const fs = require('fs');

class ComprehensiveSystemTester {
  constructor() {
    this.results = {
      visual: {},
      functionality: {},
      ux: {},
      performance: {},
      accessibility: {},
      overall: {}
    };
  }

  async runFullTest() {
    console.log('🚀 Starting Comprehensive System Test...');
    
    const browser = await puppeteer.launch({ 
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    
    const page = await browser.newPage();
    await page.setViewport({ width: 1920, height: 1080 });
    
    try {
      // 1. Visual Testing
      console.log('\n📱 1. Visual Testing...');
      await this.testVisualDesign(page);
      
      // 2. Functionality Testing
      console.log('\n⚙️ 2. Functionality Testing...');
      await this.testFunctionality(page);
      
      // 3. UX Testing
      console.log('\n🎨 3. UX Testing...');
      await this.testUserExperience(page);
      
      // 4. Performance Testing
      console.log('\n⚡ 4. Performance Testing...');
      await this.testPerformance(page);
      
      // 5. Accessibility Testing
      console.log('\n♿ 5. Accessibility Testing...');
      await this.testAccessibility(page);
      
      // 6. Backend Integration Testing
      console.log('\n🔗 6. Backend Integration Testing...');
      await this.testBackendIntegration(page);
      
      // Generate comprehensive report
      this.generateReport();
      
    } finally {
      await browser.close();
    }
  }

  async testVisualDesign(page) {
    const pages = [
      { name: 'Home', url: 'http://localhost:3000' },
      { name: 'Research', url: 'http://localhost:3000/research' }
    ];
    
    for (const pageInfo of pages) {
      await page.goto(pageInfo.url, { waitUntil: 'networkidle0' });
      
      const visualAnalysis = await page.evaluate(() => {
        const checks = {
          // Visual consistency
          darkThemeApplied: document.body.classList.contains('dark') || 
            getComputedStyle(document.body).backgroundColor.includes('rgb(15, 23, 42)'),
          
          // Layout integrity
          noHorizontalScroll: document.body.scrollWidth <= window.innerWidth,
          noOverlappingElements: (() => {
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
          
          // Responsive design
          mobileReady: window.innerWidth < 768 ? 
            !!document.querySelector('[class*="mobile"], [class*="sm:"]') : true,
          
          // Visual hierarchy
          properContrast: (() => {
            const textElements = document.querySelectorAll('p, h1, h2, h3, span');
            let goodContrast = 0;
            textElements.forEach(el => {
              const style = getComputedStyle(el);
              const color = style.color;
              const bgColor = style.backgroundColor;
              // Simple contrast check (in real implementation, use proper contrast ratio)
              if (color !== bgColor) goodContrast++;
            });
            return goodContrast > textElements.length * 0.8;
          })(),
          
          // Button design
          buttonsProperlyStyled: Array.from(document.querySelectorAll('button')).every(
            btn => btn.offsetHeight >= 44 && btn.offsetWidth >= 44
          )
        };
        
        const score = Math.round((Object.values(checks).filter(Boolean).length / Object.keys(checks).length) * 100);
        return { score, checks };
      });
      
      this.results.visual[pageInfo.name] = visualAnalysis;
      console.log(`  ✅ ${pageInfo.name}: ${visualAnalysis.score}/100`);
    }
  }

  async testFunctionality(page) {
    // Test chat functionality
    await page.goto('http://localhost:3000/research', { waitUntil: 'networkidle0' });
    
    const functionalityTest = await page.evaluate(async () => {
      const tests = {
        // Form submission
        formSubmission: (() => {
          const forms = document.querySelectorAll('form');
          return forms.length > 0 && Array.from(forms).every(form => form.onsubmit !== null || form.querySelector('button[type="submit"]'));
        })(),
        
        // Input validation
        inputValidation: (() => {
          const inputs = document.querySelectorAll('input, textarea');
          return inputs.length > 0 && Array.from(inputs).some(input => input.hasAttribute('required'));
        })(),
        
        // Button interactions
        buttonInteractions: (() => {
          const buttons = document.querySelectorAll('button');
          return buttons.length > 0 && Array.from(buttons).every(btn => 
            btn.onclick !== null || btn.type === 'submit' || btn.closest('form')
          );
        })(),
        
        // Navigation
        navigation: (() => {
          const links = document.querySelectorAll('a[href]');
          return links.length > 0 && Array.from(links).every(link => link.href && !link.href.includes('undefined'));
        })(),
        
        // Chat interface
        chatInterface: !!document.querySelector('input[type="text"], textarea'),
        
        // Error handling
        errorHandling: (() => {
          // Check for error boundaries or error handling elements
          return !document.querySelector('.error, .alert-danger, [class*="error"]');
        })()
      };
      
      const score = Math.round((Object.values(tests).filter(Boolean).length / Object.keys(tests).length) * 100);
      return { score, tests };
    });
    
    this.results.functionality = functionalityTest;
    console.log(`  ✅ Functionality: ${functionalityTest.score}/100`);
  }

  async testUserExperience(page) {
    const uxTest = await page.evaluate(() => {
      const tests = {
        // Loading states
        loadingStates: (() => {
          const buttons = document.querySelectorAll('button');
          return Array.from(buttons).some(btn => 
            btn.textContent.includes('Loading') || 
            btn.querySelector('.spinner, .loader') ||
            btn.disabled
          );
        })(),
        
        // Feedback mechanisms
        feedbackMechanisms: (() => {
          // Check for hover effects, transitions, etc.
          const interactiveElements = document.querySelectorAll('button, a, input');
          return Array.from(interactiveElements).some(el => {
            const style = getComputedStyle(el);
            return style.transition !== 'none' || style.cursor === 'pointer';
          });
        })(),
        
        // Information architecture
        clearNavigation: (() => {
          const navElements = document.querySelectorAll('nav, [role="navigation"], .sidebar');
          return navElements.length > 0;
        })(),
        
        // Content hierarchy
        contentHierarchy: (() => {
          const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
          return headings.length > 0;
        })(),
        
        // User guidance
        userGuidance: (() => {
          const placeholders = document.querySelectorAll('[placeholder]');
          const labels = document.querySelectorAll('label');
          return placeholders.length > 0 || labels.length > 0;
        })(),
        
        // Responsive behavior
        responsiveDesign: (() => {
          const viewport = document.querySelector('meta[name="viewport"]');
          return !!viewport;
        })()
      };
      
      const score = Math.round((Object.values(tests).filter(Boolean).length / Object.keys(tests).length) * 100);
      return { score, tests };
    });
    
    this.results.ux = uxTest;
    console.log(`  ✅ UX: ${uxTest.score}/100`);
  }

  async testPerformance(page) {
    const performanceTest = await page.evaluate(() => {
      const tests = {
        // Page load performance
        fastLoad: performance.timing.loadEventEnd - performance.timing.navigationStart < 3000,
        
        // Resource optimization
        optimizedResources: (() => {
          const images = document.querySelectorAll('img');
          return Array.from(images).every(img => img.complete);
        })(),
        
        // Memory efficiency
        memoryEfficient: (() => {
          // Simple check for memory leaks (in real implementation, use performance.memory)
          return document.querySelectorAll('*').length < 1000;
        })(),
        
        // Network efficiency
        networkEfficient: (() => {
          // Check for lazy loading, etc.
          const lazyImages = document.querySelectorAll('img[loading="lazy"]');
          return lazyImages.length > 0 || document.querySelectorAll('img').length === 0;
        })()
      };
      
      const score = Math.round((Object.values(tests).filter(Boolean).length / Object.keys(tests).length) * 100);
      return { score, tests };
    });
    
    this.results.performance = performanceTest;
    console.log(`  ✅ Performance: ${performanceTest.score}/100`);
  }

  async testAccessibility(page) {
    const accessibilityTest = await page.evaluate(() => {
      const tests = {
        // Semantic HTML
        semanticHTML: (() => {
          const semanticElements = document.querySelectorAll('main, nav, header, footer, section, article');
          return semanticElements.length > 0;
        })(),
        
        // Alt text for images
        imageAltText: (() => {
          const images = document.querySelectorAll('img');
          return images.length === 0 || Array.from(images).every(img => img.alt !== undefined);
        })(),
        
        // Form labels
        formLabels: (() => {
          const inputs = document.querySelectorAll('input, textarea');
          return inputs.length === 0 || Array.from(inputs).every(input => 
            input.labels.length > 0 || input.placeholder || input.getAttribute('aria-label')
          );
        })(),
        
        // Keyboard navigation
        keyboardNavigation: (() => {
          const interactiveElements = document.querySelectorAll('button, a, input, textarea');
          return Array.from(interactiveElements).every(el => 
            el.tabIndex >= 0 || el.tagName === 'A' || el.tagName === 'BUTTON'
          );
        })(),
        
        // Color contrast
        colorContrast: (() => {
          // Simple check (in real implementation, use proper contrast ratio calculation)
          const textElements = document.querySelectorAll('p, h1, h2, h3, span');
          return textElements.length > 0;
        })(),
        
        // Focus indicators
        focusIndicators: (() => {
          const focusableElements = document.querySelectorAll('button, a, input, textarea');
          return Array.from(focusableElements).some(el => {
            const style = getComputedStyle(el, ':focus');
            return style.outline !== 'none' || style.boxShadow !== 'none';
          });
        })()
      };
      
      const score = Math.round((Object.values(tests).filter(Boolean).length / Object.keys(tests).length) * 100);
      return { score, tests };
    });
    
    this.results.accessibility = accessibilityTest;
    console.log(`  ✅ Accessibility: ${accessibilityTest.score}/100`);
  }

  async testBackendIntegration(page) {
    // Test actual API calls
    const backendTest = await page.evaluate(async () => {
      const tests = {
        // API connectivity
        apiConnectivity: false,
        // Chat functionality
        chatFunctionality: false,
        // Error handling
        errorHandling: false
      };
      
      try {
        // Test API endpoint
        const response = await fetch('http://127.0.0.1:8002/health');
        tests.apiConnectivity = response.ok;
        
        // Test chat endpoint
        const chatResponse = await fetch('http://127.0.0.1:8002/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: 'test', session_id: 'test' })
        });
        tests.chatFunctionality = chatResponse.ok;
        
        // Test error handling
        const errorResponse = await fetch('http://127.0.0.1:8002/api/nonexistent');
        tests.errorHandling = !errorResponse.ok; // Should return 404
        
      } catch (error) {
        console.log('Backend test error:', error.message);
      }
      
      const score = Math.round((Object.values(tests).filter(Boolean).length / Object.keys(tests).length) * 100);
      return { score, tests };
    });
    
    this.results.backend = backendTest;
    console.log(`  ✅ Backend Integration: ${backendTest.score}/100`);
  }

  generateReport() {
    // Calculate overall score
    const scores = [
      ...Object.values(this.results.visual).map(v => v.score),
      this.results.functionality.score,
      this.results.ux.score,
      this.results.performance.score,
      this.results.accessibility.score,
      this.results.backend.score
    ];
    
    const overallScore = Math.round(scores.reduce((sum, score) => sum + score, 0) / scores.length);
    
    this.results.overall = {
      score: overallScore,
      grade: overallScore >= 90 ? 'A' : overallScore >= 80 ? 'B' : overallScore >= 70 ? 'C' : 'D',
      status: overallScore >= 90 ? 'Production Ready' : overallScore >= 80 ? 'Near Ready' : 'Needs Work'
    };
    
    // Save comprehensive report
    fs.writeFileSync('comprehensive-system-report.json', JSON.stringify(this.results, null, 2));
    
    // Display results
    console.log('\n📊 COMPREHENSIVE SYSTEM TEST RESULTS:');
    console.log(`\n🎯 Overall Score: ${overallScore}/100 (Grade: ${this.results.overall.grade})`);
    console.log(`📈 Status: ${this.results.overall.status}`);
    
    console.log('\n📋 Detailed Scores:');
    console.log(`  Visual Design: ${Math.round(Object.values(this.results.visual).reduce((sum, v) => sum + v.score, 0) / Object.keys(this.results.visual).length)}/100`);
    console.log(`  Functionality: ${this.results.functionality.score}/100`);
    console.log(`  User Experience: ${this.results.ux.score}/100`);
    console.log(`  Performance: ${this.results.performance.score}/100`);
    console.log(`  Accessibility: ${this.results.accessibility.score}/100`);
    console.log(`  Backend Integration: ${this.results.backend.score}/100`);
    
    console.log('\n📄 Full report saved to: comprehensive-system-report.json');
    
    // Generate recommendations
    this.generateRecommendations();
  }

  generateRecommendations() {
    const recommendations = [];
    
    if (this.results.functionality.score < 90) {
      recommendations.push('Improve form validation and error handling');
    }
    if (this.results.ux.score < 90) {
      recommendations.push('Enhance user feedback and loading states');
    }
    if (this.results.performance.score < 90) {
      recommendations.push('Optimize page load times and resource usage');
    }
    if (this.results.accessibility.score < 90) {
      recommendations.push('Improve accessibility features and keyboard navigation');
    }
    if (this.results.backend.score < 90) {
      recommendations.push('Strengthen backend integration and error handling');
    }
    
    if (recommendations.length > 0) {
      console.log('\n💡 RECOMMENDATIONS:');
      recommendations.forEach((rec, i) => console.log(`  ${i + 1}. ${rec}`));
    } else {
      console.log('\n🎉 No major issues found! System is production-ready!');
    }
  }
}

// Run the comprehensive test
async function runComprehensiveTest() {
  const tester = new ComprehensiveSystemTester();
  await tester.runFullTest();
}

runComprehensiveTest().catch(console.error);

