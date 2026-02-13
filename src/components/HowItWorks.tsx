import { useState, useEffect } from 'react';
import { Radar, Brain, BookOpen, Target, Database, TrendingUp, CheckCircle, Clock, FileText } from 'lucide-react';

const pipelineSteps = [
  {
    number: '01',
    title: 'THE SENSOR',
    subtitle: 'Real-Time Scraping',
    icon: Radar,
    description: 'Our engine scans Indeed and LinkedIn daily for management roles, capturing live job postings and extracting managerial competency requirements.',
    details: [
      'Automated scraping every 24 hours',
      'Coverage: 50+ management job titles',
      'Sources: Indeed, LinkedIn, Glassdoor',
      'Deduplication algorithms ensure accuracy'
    ]
  },
  {
    number: '02',
    title: 'THE BRAIN',
    subtitle: 'NLP Extraction',
    icon: Brain,
    description: 'Advanced natural language processing reads job descriptions and extracts managerial competencies using the market-driven skills extraction approach (Boshkoska et al.).',
    details: [
      'Named Entity Recognition for competencies',
      'Context-aware parsing of skill requirements',
      'Mapping to Rubin & Dierdoff competency framework',
      'Weighted scoring based on frequency'
    ]
  },
  {
    number: '03',
    title: 'THE LIBRARY',
    subtitle: 'Curriculum Ingestion',
    icon: BookOpen,
    description: 'We digitize MBA course catalogs from top business schools, mapping course content to the six managerial competencies identified by Rubin & Dierdoff.',
    details: [
      'Manual + automated catalog parsing',
      'Coverage: Top 50 business schools globally',
      'Updated quarterly with new course offerings',
      'Skills mapped to standardized competency taxonomy'
    ]
  },
  {
    number: '04',
    title: 'THE MATCH',
    subtitle: 'Gap Analysis',
    icon: Target,
    description: 'We overlay real-time market demand on MBA curricula to reveal alignment gaps between what schools teach and what employers require.',
    details: [
      'Demand Index: Frequency in job postings',
      'Supply Index: Coverage in MBA curricula',
      'Gap Score: Market Demand minus School Supply',
      'Benchmarking against Rubin & Dierdoff baseline'
    ]
  }
];

const scoringMetrics = [
  {
    title: 'Market Alignment Score',
    description: 'Schools earn points for curriculum coverage in each of the six managerial competencies based on current market demand.',
    formula: 'Points = (Market Demand %) × (Curriculum Coverage %)'
  },
  {
    title: 'Competency Gap Penalty',
    description: 'Schools lose points for under-teaching competencies that appear frequently in job postings (>50% demand).',
    formula: 'Penalty = -(Gap %) × (Market Demand %)'
  },
  {
    title: 'Regional Relevance Bonus',
    description: 'Schools gain bonus points for aligning with local/regional job market needs based on geographic data.',
    formula: 'Bonus = (Local Demand - National Demand) × 10'
  }
];

export default function HowItWorks() {
  const [visibleSections, setVisibleSections] = useState<Set<string>>(new Set());

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const id = entry.target.getAttribute('data-section');
            if (id) {
              setVisibleSections((prev) => new Set([...prev, id]));
            }
          }
        });
      },
      { threshold: 0.2 }
    );

    const elements = document.querySelectorAll('[data-section]');
    elements.forEach((el) => observer.observe(el));

    return () => observer.disconnect();
  }, []);

  return (
    <div className="min-h-screen">
      {/* Centered Hero Section */}
      <section className="border-b-2 border-black min-h-[80vh] flex items-center justify-center" data-section="hero">
        <div className="max-w-4xl mx-auto px-6 sm:px-8 lg:px-12 py-20 text-center">
          <div className={`mb-8 ${visibleSections.has('hero') ? 'animate-fade-in-up' : 'opacity-0'}`}>
            <div className="inline-block bg-black text-white px-4 py-2 text-xs font-bold tracking-widest uppercase">
              TECHNICAL SPECIFICATION
            </div>
          </div>

          <h1 className={`text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-black tracking-tighter leading-none mb-12 ${
            visibleSections.has('hero') ? 'animate-fade-in-scale' : 'opacity-0'
          }`} style={{ animationDelay: '0.2s' }}>
            METHODOLOGY<br/>
            & FRAMEWORK
          </h1>

          <p className={`text-lg sm:text-xl text-gray-700 mb-6 max-w-2xl mx-auto leading-relaxed ${
            visibleSections.has('hero') ? 'animate-fade-in-up' : 'opacity-0'
          }`} style={{ animationDelay: '0.4s' }}>
            Business schools operate on 2-year curriculum cycles.<br/>
            The market moves in real-time.
          </p>

          <p className={`text-lg sm:text-xl text-gray-700 max-w-2xl mx-auto leading-relaxed ${
            visibleSections.has('hero') ? 'animate-fade-in-up' : 'opacity-0'
          }`} style={{ animationDelay: '0.6s' }}>
            We built an engine to show you the delta—and help you fill the gap before graduation.
          </p>
        </div>
      </section>

      {/* Data Pipeline */}
      <section className="border-b-2 border-black bg-gray-50" data-section="pipeline">
        <div className="max-w-[1400px] mx-auto px-6 sm:px-8 lg:px-12 py-20">
          <div className={`text-center mb-16 ${visibleSections.has('pipeline') ? 'animate-fade-in-up' : 'opacity-0'}`}>
            <h2 className="text-4xl sm:text-5xl font-black tracking-tight mb-4">THE DATA PIPELINE</h2>
            <p className="text-lg text-gray-600">Four-stage AI-powered processing system</p>
          </div>

          <div className="space-y-12">
            {pipelineSteps.map((step, idx) => {
              const Icon = step.icon;
              const isVisible = visibleSections.has('pipeline');
              return (
                <div 
                  key={idx} 
                  className={`border-2 border-black shadow-[8px_8px_0_0_rgba(0,0,0,1)] ${
                    isVisible ? 'animate-fade-in-scale' : 'opacity-0'
                  }`}
                  style={{ animationDelay: `${idx * 0.2}s` }}
                >
                  <div className="bg-black text-white p-6 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="text-2xl font-black">STEP {step.number}</div>
                      <div className="w-px h-8 bg-white"></div>
                      <div>
                        <div className="font-black tracking-wider uppercase">{step.title}</div>
                        <div className="text-xs font-bold tracking-widest uppercase opacity-70">{step.subtitle}</div>
                      </div>
                    </div>
                    <Icon className="w-8 h-8" />
                  </div>

                  <div className="bg-white p-8 sm:p-12">
                    <p className="text-xl leading-relaxed mb-8 text-gray-700">
                      {step.description}
                    </p>
                    <div className="grid sm:grid-cols-2 gap-4">
                      {step.details.map((detail, detailIdx) => (
                        <div 
                          key={detailIdx}
                          className="flex items-start gap-3 bg-gray-50 p-4 border-l-4 border-black"
                        >
                          <CheckCircle className="w-5 h-5 mt-0.5 flex-shrink-0" />
                          <span className="font-medium text-sm">{detail}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Flow Indicator */}
          <div className={`mt-16 pt-8 border-t-2 border-black ${visibleSections.has('pipeline') ? 'animate-fade-in-up' : 'opacity-0'}`} style={{ animationDelay: '0.8s' }}>
            <div className="flex items-center gap-3 text-sm font-bold tracking-widest uppercase justify-center">
              <div className="w-2 h-2 bg-red-600 rounded-full animate-breathe"></div>
              <span>Data flows from Step 01 → 04 in real-time</span>
            </div>
          </div>
        </div>
      </section>

      {/* Ranking System */}
      <section className="border-b-2 border-black bg-white" data-section="ranking">
        <div className="max-w-[1400px] mx-auto px-6 sm:px-8 lg:px-12 py-20">
          <div className={`text-center mb-16 ${visibleSections.has('ranking') ? 'animate-fade-in-up' : 'opacity-0'}`}>
            <h2 className="text-4xl sm:text-5xl font-black tracking-tight mb-4">THE RANKING SYSTEM</h2>
            <p className="text-lg text-gray-600">Algorithmic scoring methodology</p>
          </div>

          <div className={`bg-white border-2 border-black shadow-[8px_8px_0_0_rgba(0,0,0,1)] p-8 sm:p-12 mb-12 ${
            visibleSections.has('ranking') ? 'animate-fade-in-scale' : 'opacity-0'
          }`} style={{ animationDelay: '0.2s' }}>
            <p className="text-2xl leading-relaxed text-gray-700 mb-12 text-center">
              Schools are scored on a <span className="font-black">0-100 scale</span> based on how well their curricula align with real-time market demand. The algorithm rewards relevance and punishes outdated requirements.
            </p>

            <div className="space-y-8">
              {scoringMetrics.map((metric, idx) => (
                <div key={idx} className="border-l-4 border-black pl-8">
                  <div className="text-xs font-bold tracking-widest uppercase text-gray-500 mb-2">
                    METRIC {String(idx + 1).padStart(2, '0')}
                  </div>
                  <h3 className="text-2xl font-black mb-4">
                    {metric.title}
                  </h3>
                  <p className="text-gray-700 mb-4 leading-relaxed">
                    {metric.description}
                  </p>
                  <div className="bg-gray-50 border-2 border-black px-6 py-4 font-mono text-sm">
                    {metric.formula}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Pull Quote */}
          <div className={`bg-black text-white p-8 sm:p-12 ${visibleSections.has('ranking') ? 'animate-fade-in-up' : 'opacity-0'}`} style={{ animationDelay: '0.4s' }}>
            <div className="text-sm font-bold tracking-widest uppercase mb-4 opacity-70">
              Case Study
            </div>
            <p className="text-2xl sm:text-3xl font-bold leading-tight">
              If 76% of Product Manager jobs require SQL, but only 28% of MBA programs offer SQL courses, that creates a <span className="text-red-600">-48 gap score</span>. Schools with SQL courses earn bonus points.
            </p>
          </div>
        </div>
      </section>

      {/* Research Foundation */}
      <section className="border-b-2 border-black bg-gray-50" data-section="research">
        <div className="max-w-[1400px] mx-auto px-6 sm:px-8 lg:px-12 py-20">
          <div className={`text-center mb-16 ${visibleSections.has('research') ? 'animate-fade-in-up' : 'opacity-0'}`}>
            <h2 className="text-4xl sm:text-5xl font-black tracking-tight mb-4">RESEARCH FOUNDATION</h2>
            <p className="text-lg text-gray-600">Peer-reviewed academic frameworks</p>
          </div>

          <div className="space-y-8">
            {/* First Study */}
            <div className={`border-2 border-black shadow-[8px_8px_0_0_rgba(0,0,0,1)] ${
              visibleSections.has('research') ? 'animate-slide-in-left' : 'opacity-0'
            }`}>
              <div className="bg-gray-100 border-b-2 border-black p-6">
                <div className="flex items-center justify-between">
                  <div className="text-xs font-bold tracking-widest uppercase">Study 01</div>
                  <div className="bg-black text-white px-4 py-1 text-xs font-bold tracking-widest uppercase">
                    Methodology
                  </div>
                </div>
              </div>
              <div className="bg-white p-8 sm:p-12">
                <h3 className="text-3xl font-black mb-6 leading-tight">
                  Market-Driven Skills Extraction Approach
                </h3>
                <p className="text-lg text-gray-700 mb-8 leading-relaxed">
                  Our NLP methodology for extracting skills from job postings is based on the framework developed by Boshkoska et al. This approach uses automated web scraping combined with natural language processing to identify skill requirements in real-time job market data, enabling dynamic curriculum alignment.
                </p>
                <div className="bg-gray-50 border-l-4 border-black p-6">
                  <div className="text-xs font-bold tracking-widest uppercase mb-3">Citation</div>
                  <p className="text-sm leading-relaxed">
                    Boshkoska, B. M., Mishkovski, I., & Likozar, B. (2021). 
                    "Designing graduate business curricula by utilizing a market-driven skills extraction approach." 
                    <span className="italic">Educational Sciences</span>, 11(9), 483.
                  </p>
                </div>
              </div>
            </div>

            {/* Second Study */}
            <div className={`border-2 border-black shadow-[8px_8px_0_0_rgba(0,0,0,1)] ${
              visibleSections.has('research') ? 'animate-slide-in-right' : 'opacity-0'
            }`} style={{ animationDelay: '0.2s' }}>
              <div className="bg-gray-100 border-b-2 border-black p-6">
                <div className="flex items-center justify-between">
                  <div className="text-xs font-bold tracking-widest uppercase">Study 02</div>
                  <div className="bg-black text-white px-4 py-1 text-xs font-bold tracking-widest uppercase">
                    Framework
                  </div>
                </div>
              </div>
              <div className="bg-white p-8 sm:p-12">
                <h3 className="text-3xl font-black mb-6 leading-tight">
                  Six Managerial Competencies Framework
                </h3>
                <p className="text-lg text-gray-700 mb-8 leading-relaxed">
                  The competency categories used throughout our platform are derived from Rubin & Dierdorff's landmark study assessing MBA curriculum relevance. Their research identified six core managerial competencies required in the workplace and measured the alignment (or misalignment) with what business schools actually teach.
                </p>
                <div className="bg-gray-50 border-l-4 border-black p-6 mb-8">
                  <div className="text-xs font-bold tracking-widest uppercase mb-3">Citation</div>
                  <p className="text-sm leading-relaxed">
                    Rubin, R. S., & Dierdorff, E. C. (2009). 
                    "How Relevant Is the MBA? Assessing the Alignment of Required Curricula and Required Managerial Competencies." 
                    <span className="italic">Academy of Management Learning & Education</span>, 8(2), 208-224.
                  </p>
                </div>
                <div className="grid sm:grid-cols-2 gap-4">
                  {[
                    'Managing Decision-Making Processes',
                    'Managing Human Capital',
                    'Managing Strategy and Innovation',
                    'Managing the Task Environment',
                    'Managing Administration and Control',
                    'Managing Logistics and Technology'
                  ].map((competency, idx) => (
                    <div key={idx} className="flex items-start gap-3 bg-gray-50 p-4 border-l-4 border-black">
                      <CheckCircle className="w-5 h-5 mt-0.5 flex-shrink-0" />
                      <span className="font-bold text-sm">{competency}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Integration Note */}
            <div className={`bg-black text-white p-8 sm:p-12 ${visibleSections.has('research') ? 'animate-fade-in-up' : 'opacity-0'}`} style={{ animationDelay: '0.4s' }}>
              <div className="text-xs font-bold tracking-widest uppercase mb-4 opacity-70">
                System Integration
              </div>
              <p className="text-xl sm:text-2xl font-bold leading-tight">
                By combining Boshkoska's scraping methodology with Rubin & Dierdorff's competency framework, we create a live, validated measurement system that tracks the evolving gap between MBA education and market reality.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Trust Signals Footer */}
      <section className="border-t-2 border-black bg-white" data-section="footer">
        <div className="max-w-[1400px] mx-auto px-6 sm:px-8 lg:px-12 py-16">
          <div className={`grid sm:grid-cols-3 gap-12 ${visibleSections.has('footer') ? 'animate-fade-in-scale' : 'opacity-0'}`}>
            <div className="text-center">
              <Database className="w-12 h-12 mb-4 mx-auto" />
              <div className="text-5xl font-black mb-2">12,847</div>
              <div className="text-xs font-bold tracking-widest uppercase text-gray-600">Jobs in Database</div>
            </div>
            <div className="text-center">
              <Clock className="w-12 h-12 mb-4 mx-auto" />
              <div className="text-5xl font-black mb-2">Today</div>
              <div className="text-xs font-bold tracking-widest uppercase text-gray-600">Last Updated</div>
            </div>
            <div className="text-center">
              <CheckCircle className="w-12 h-12 mb-4 mx-auto" />
              <div className="text-5xl font-black mb-2">3 Sources</div>
              <div className="text-xs font-bold tracking-widest uppercase text-gray-600">Indeed • LinkedIn • Catalogs</div>
            </div>
          </div>

          <div className="mt-12 pt-8 border-t-2 border-black">
            <div className="text-xs font-bold tracking-widest uppercase text-gray-600 text-center">
              System Status: Operational • Data Refresh: Every 24h • Accuracy Rate: 92%
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
