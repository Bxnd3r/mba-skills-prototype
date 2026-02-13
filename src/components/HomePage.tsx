import { useState, useEffect, useRef } from 'react';
import { Search, TrendingUp, BookOpen, Award, ArrowRight, ChevronLeft, ChevronRight } from 'lucide-react';
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer, Legend, Tooltip } from 'recharts';

// --- IMPORTS ---
// 1. Job Data
import realJobsData from '../data/jobs_db copy.json';

// 2. School Curriculum Data
// Make sure this file exists in src/data/
import schoolData from '../data/raw_school_data copy.json';

const skillsData = [
  { skill: 'Decision-Making', school: 65, comparison: 85, fullName: 'Managing Decision-Making Processes' },
  { skill: 'Human Capital', school: 72, comparison: 78, fullName: 'Managing Human Capital' },
  { skill: 'Strategy & Innovation', school: 88, comparison: 82, fullName: 'Managing Strategy and Innovation' },
  { skill: 'Task Environment', school: 58, comparison: 90, fullName: 'Managing the Task Environment' },
  { skill: 'Admin & Control', school: 45, comparison: 68, fullName: 'Managing Administration and Control' },
  { skill: 'Logistics & Tech', school: 38, comparison: 92, fullName: 'Managing Logistics and Technology' },
];

const mockSchools = [
  'Northwestern University Kellogg',
  'Harvard Business School',
  'Stanford Graduate School of Business',
  'MIT Sloan School of Management',
  'Wharton School (UPenn)',
];

// NOTE: We replaced mockCourses with schoolData.curriculum below!

const mockSchoolRankings = [
  { rank: 1, school: 'MIT Sloan School of Management', nationalScore: 94, logistics: 98, strategy: 92, decision: 90 },
  { rank: 2, school: 'Stanford Graduate School of Business', nationalScore: 92, logistics: 89, strategy: 96, decision: 94 },
  { rank: 3, school: 'Northwestern University Kellogg', nationalScore: 89, logistics: 85, strategy: 94, decision: 91 },
  { rank: 4, school: 'Harvard Business School', nationalScore: 88, logistics: 82, strategy: 93, decision: 92 },
  { rank: 5, school: 'Wharton School (UPenn)', nationalScore: 87, logistics: 84, strategy: 90, decision: 89 },
  { rank: 6, school: 'UC Berkeley Haas', nationalScore: 85, logistics: 90, strategy: 87, decision: 86 },
  { rank: 7, school: 'Columbia Business School', nationalScore: 84, logistics: 81, strategy: 89, decision: 88 },
  { rank: 8, school: 'Chicago Booth School of Business', nationalScore: 83, logistics: 79, strategy: 91, decision: 87 },
];

export default function HomePage() {
  const [currentSchoolIndex, setCurrentSchoolIndex] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSchool, setSelectedSchool] = useState(mockSchools[0]);
  const [comparisonType, setComparisonType] = useState<'local' | 'national' | 'school' | 'rubin'>('national');
  const [sortBy, setSortBy] = useState<string>('highest-national');
  const [visibleSections, setVisibleSections] = useState<Set<string>>(new Set());
  const radarRef = useRef<HTMLDivElement>(null);

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

  const nextSchool = () => {
    setCurrentSchoolIndex((prev) => (prev + 1) % mockSchools.length);
    setSelectedSchool(mockSchools[(currentSchoolIndex + 1) % mockSchools.length]);
  };

  const prevSchool = () => {
    setCurrentSchoolIndex((prev) => (prev - 1 + mockSchools.length) % mockSchools.length);
    setSelectedSchool(mockSchools[(currentSchoolIndex - 1 + mockSchools.length) % mockSchools.length]);
  };

  const scrollToRadar = () => {
    radarRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      setSelectedSchool(searchQuery);
    }
  };

  const getSortedSchools = () => {
    const schools = [...mockSchoolRankings];
    if (sortBy === 'highest-national') return schools.sort((a, b) => b.nationalScore - a.nationalScore);
    if (sortBy === 'lowest-national') return schools.sort((a, b) => a.nationalScore - b.nationalScore);
    if (sortBy.includes('logistics')) return schools.sort((a, b) => sortBy.includes('highest') ? b.logistics - a.logistics : a.logistics - b.logistics);
    if (sortBy.includes('strategy')) return schools.sort((a, b) => sortBy.includes('highest') ? b.strategy - a.strategy : a.strategy - b.strategy);
    if (sortBy.includes('decision')) return schools.sort((a, b) => sortBy.includes('highest') ? b.decision - a.decision : a.decision - b.decision);
    return schools;
  };

  // Helper to parse course strings like "BUS 101: Intro to Business"
  const parseCourse = (courseString: string) => {
    const parts = courseString.split(':');
    if (parts.length > 1) {
        return { code: parts[0], name: parts.slice(1).join(':') };
    }
    return { code: '---', name: courseString };
  };

  return (
    <div className="min-h-screen">
      {/* Centered Hero Section */}
      <section className="border-b-2 border-black min-h-[80vh] flex items-center justify-center" data-section="hero">
        <div className="max-w-4xl mx-auto px-6 sm:px-8 lg:px-12 py-20 text-center">
          <div className={`mb-8 ${visibleSections.has('hero') ? 'animate-fade-in-up' : 'opacity-0'}`}>
            <div className="inline-flex items-center gap-2 bg-black text-white px-4 py-2 text-xs font-bold tracking-widest uppercase">
              <div className="w-1.5 h-1.5 bg-red-600 rounded-full animate-breathe"></div>
              {/* Dynamic Job Count */}
              Live Data — {realJobsData.length} Jobs Analyzed Today
            </div>
          </div>

          <h1 className={`text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-black tracking-tighter leading-none mb-12 ${
            visibleSections.has('hero') ? 'animate-fade-in-scale' : 'opacity-0'
          }`} style={{ animationDelay: '0.2s' }}>
            COMPARE A<br/>
            BUSINESS SCHOOL<br/>
            TO THE MARKET
          </h1>

          <p className={`text-lg sm:text-xl text-gray-700 mb-12 max-w-2xl mx-auto leading-relaxed ${
            visibleSections.has('hero') ? 'animate-fade-in-up' : 'opacity-0'
          }`} style={{ animationDelay: '0.4s' }}>
            Real-time alignment analysis between MBA curricula and market demand through AI-powered data processing.
          </p>

          <button
            onClick={scrollToRadar}
            className={`group inline-flex items-center gap-3 bg-black text-white px-8 py-4 text-base font-bold tracking-wider uppercase hover:bg-gray-800 transition-all shadow-[4px_4px_0_0_rgba(220,38,38,1)] hover:shadow-none hover:translate-x-1 hover:translate-y-1 ${
              visibleSections.has('hero') ? 'animate-fade-in-scale' : 'opacity-0'
            }`}
            style={{ animationDelay: '0.6s' }}
          >
            View Analysis
            <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </button>
        </div>
      </section>

      {/* Radar Chart Section with Carousel & Sidebar */}
      <section ref={radarRef} className="border-b-2 border-black bg-gray-50" data-section="radar">
        <div className="max-w-[1600px] mx-auto px-6 sm:px-8 lg:px-12 py-20">
          <div className="grid lg:grid-cols-3 gap-8">
            {/* Left: Radar Chart Carousel */}
            <div className="lg:col-span-2">
              <div className={visibleSections.has('radar') ? 'animate-slide-in-left' : 'opacity-0'}>
                {/* Search Bar Above Radar */}
                <div className="mb-8">
                  <form onSubmit={handleSearch} className="relative">
                    <div className="bg-white border-2 border-black p-6 shadow-[8px_8px_0_0_rgba(0,0,0,1)]">
                      <label className="block text-sm font-bold tracking-wider uppercase mb-3">
                        Search Institution
                      </label>
                      <div className="flex gap-2">
                        <input
                          type="text"
                          value={searchQuery}
                          onChange={(e) => setSearchQuery(e.target.value)}
                          placeholder="Enter school name..."
                          className="flex-1 border-2 border-black px-4 py-3 text-base bg-white focus:outline-none focus:ring-4 focus:ring-gray-300"
                        />
                        <button
                          type="submit"
                          className="bg-black text-white px-6 py-3 text-base font-bold tracking-wider uppercase hover:bg-gray-800 transition-colors border-2 border-black"
                        >
                          <Search className="w-5 h-5" />
                        </button>
                      </div>
                    </div>
                  </form>
                </div>

                {/* Radar Chart with Breathing Animation */}
                <div className="bg-white border-2 border-black shadow-[8px_8px_0_0_rgba(0,0,0,1)] overflow-hidden animate-breathe">
                  <div className="border-b-2 border-black p-6 bg-gray-50">
                    <div className="flex items-center justify-between mb-4">
                      <h2 className="text-2xl font-black tracking-tight">{selectedSchool}</h2>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={prevSchool}
                          className="p-2 bg-black text-white hover:bg-gray-800 transition-colors"
                        >
                          <ChevronLeft className="w-5 h-5" />
                        </button>
                        <button
                          onClick={nextSchool}
                          className="p-2 bg-black text-white hover:bg-gray-800 transition-colors"
                        >
                          <ChevronRight className="w-5 h-5" />
                        </button>
                      </div>
                    </div>
                    
                    {/* Carousel Dots */}
                    <div className="flex gap-2 justify-center">
                      {mockSchools.map((_, index) => (
                        <div
                          key={index}
                          className={`carousel-dot ${index === currentSchoolIndex ? 'active' : ''}`}
                        />
                      ))}
                    </div>
                  </div>
                  
                  <div className="p-8 bg-white">
                    <ResponsiveContainer width="100%" height={500}>
                      <RadarChart data={skillsData}>
                        <PolarGrid stroke="#d1d5db" strokeWidth={1.5} />
                        <PolarAngleAxis 
                          dataKey="skill" 
                          stroke="#374151" 
                          style={{ fontSize: '12px', fontWeight: 'bold' }} 
                        />
                        <PolarRadiusAxis 
                          stroke="#6b7280" 
                          style={{ fontSize: '11px', fontWeight: 'bold' }} 
                        />
                        <Radar 
                          name="School" 
                          dataKey="school" 
                          stroke="#6b7280" 
                          fill="#9ca3af" 
                          fillOpacity={0.3} 
                          strokeWidth={3}
                        />
                        <Radar 
                          name="Market" 
                          dataKey="comparison" 
                          stroke="#dc2626" 
                          fill="#dc2626" 
                          fillOpacity={0.2} 
                          strokeWidth={3}
                        />
                        <Legend 
                          wrapperStyle={{ fontSize: '13px', fontWeight: 'bold' }} 
                        />
                        <Tooltip 
                          contentStyle={{ 
                            backgroundColor: 'white', 
                            border: '2px solid #000000',
                            fontSize: '12px',
                            fontWeight: 'bold'
                          }}
                        />
                      </RadarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>
            </div>

            {/* Right: Comparison Framework Sidebar */}
            <div className="lg:col-span-1">
              <div className={`sticky top-24 ${visibleSections.has('radar') ? 'animate-slide-in-right' : 'opacity-0'}`} style={{ animationDelay: '0.2s' }}>
                <div className="bg-white border-2 border-black shadow-[8px_8px_0_0_rgba(0,0,0,1)]">
                  <div className="border-b-2 border-black p-6 bg-gray-50">
                    <h3 className="text-lg font-black tracking-tight uppercase">
                      Comparison Framework
                    </h3>
                  </div>
                  
                  <div className="p-6 space-y-3">
                    {[
                      { key: 'local', label: 'Local Job Market' },
                      { key: 'national', label: 'National Job Market' },
                      { key: 'school', label: 'Second School' },
                      { key: 'rubin', label: 'Rubin & Dierdoff Study' }
                    ].map((option) => (
                      <button
                        key={option.key}
                        onClick={() => setComparisonType(option.key as any)}
                        className={`w-full text-left px-4 py-3 border-2 border-black font-bold text-sm tracking-wider uppercase transition-all hover:shadow-[4px_4px_0_0_rgba(0,0,0,1)] ${
                          comparisonType === option.key 
                            ? 'bg-gray-900 text-white shadow-[4px_4px_0_0_rgba(0,0,0,1)]' 
                            : 'bg-white hover:bg-gray-50'
                        }`}
                      >
                        {option.label}
                      </button>
                    ))}
                  </div>

                  <div className="border-t-2 border-black p-6 bg-gray-50">
                    <h4 className="text-xs font-bold tracking-widest uppercase mb-4 text-gray-600">
                      Competencies Analyzed
                    </h4>
                    <div className="space-y-2">
                      {skillsData.map((item, idx) => (
                        <div key={idx} className="flex items-center justify-between text-xs">
                          <span className="font-medium">{item.skill}</span>
                          <div className="flex gap-2">
                            <span className="text-gray-600 font-bold">{item.school}</span>
                            <span className="text-gray-400">/</span>
                            <span className="text-red-600 font-bold">{item.comparison}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Course Catalog (NOW USING REAL DATA) */}
      <section className="border-b-2 border-black bg-white" data-section="courses">
        <div className="max-w-[1400px] mx-auto px-6 sm:px-8 lg:px-12 py-20">
          <div className={`text-center mb-12 ${visibleSections.has('courses') ? 'animate-fade-in-up' : 'opacity-0'}`}>
            <h2 className="text-4xl sm:text-5xl font-black tracking-tight mb-4">COURSE CATALOG</h2>
            <p className="text-lg text-gray-600">
               {schoolData.school_name || "School"} Curriculum ({schoolData.curriculum.length} Courses)
            </p>
          </div>

          <div className={visibleSections.has('courses') ? 'animate-fade-in-scale' : 'opacity-0'} style={{ animationDelay: '0.2s' }}>
            <div className="bg-white border-2 border-black shadow-[8px_8px_0_0_rgba(0,0,0,1)] overflow-hidden">
              <div className="border-b-2 border-black p-6 bg-gray-50">
                <div className="flex items-center gap-3">
                  <BookOpen className="w-5 h-5" />
                  <span className="text-sm font-bold tracking-wider uppercase">
                    Required Curriculum
                  </span>
                </div>
              </div>

              <div className="divide-y-2 divide-black max-h-[600px] overflow-y-auto">
                {schoolData.curriculum.map((course, idx) => {
                    const { code, name } = parseCourse(course.course);
                    return (
                        <div 
                            key={idx} 
                            className="grid grid-cols-12 gap-4 p-6 hover:bg-gray-50 transition-colors"
                        >
                            {/* Course Code */}
                            <div className="col-span-12 sm:col-span-2 text-sm font-black whitespace-nowrap">
                                {code}
                            </div>
                            
                            {/* Course Name */}
                            <div className="col-span-12 sm:col-span-6 text-sm font-bold text-blue-900">
                                {name}
                            </div>
                            
                            {/* Description (Used as Category replacement) */}
                            <div className="col-span-12 sm:col-span-4 text-xs text-gray-500 line-clamp-2">
                                {course.description}
                            </div>
                        </div>
                    );
                })}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* School Rankings */}
      <section id="rankings" className="border-b-2 border-black bg-gray-50" data-section="rankings">
        <div className="max-w-[1400px] mx-auto px-6 sm:px-8 lg:px-12 py-20">
          <div className={`text-center mb-12 ${visibleSections.has('rankings') ? 'animate-fade-in-up' : 'opacity-0'}`}>
            <h2 className="text-4xl sm:text-5xl font-black tracking-tight mb-4">SCHOOL RANKINGS</h2>
            <p className="text-lg text-gray-600">Market alignment performance</p>
          </div>

          <div className={visibleSections.has('rankings') ? 'animate-fade-in-scale' : 'opacity-0'} style={{ animationDelay: '0.2s' }}>
            <div className="bg-white border-2 border-black shadow-[8px_8px_0_0_rgba(0,0,0,1)] overflow-hidden">
              <div className="border-b-2 border-black p-6 bg-gray-50 flex items-center justify-between flex-wrap gap-4">
                <div className="flex items-center gap-3">
                  <Award className="w-5 h-5" />
                  <span className="text-sm font-bold tracking-wider uppercase">
                    Institutional Performance
                  </span>
                </div>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="bg-white border-2 border-black px-4 py-2 text-xs font-bold uppercase tracking-wider focus:outline-none focus:ring-4 focus:ring-gray-300"
                >
                  <option value="highest-national">Sort: National (High → Low)</option>
                  <option value="lowest-national">Sort: National (Low → High)</option>
                  <option value="highest-decision">Sort: Decision (High → Low)</option>
                  <option value="lowest-decision">Sort: Decision (Low → High)</option>
                  <option value="highest-strategy">Sort: Strategy (High → Low)</option>
                  <option value="lowest-strategy">Sort: Strategy (Low → High)</option>
                  <option value="highest-logistics">Sort: Logistics (High → Low)</option>
                  <option value="lowest-logistics">Sort: Logistics (Low → High)</option>
                </select>
              </div>

              <div className="divide-y-2 divide-black">
                <div className="grid grid-cols-12 gap-4 p-4 bg-white">
                  <div className="col-span-1 text-xs uppercase tracking-widest font-bold">Rank</div>
                  <div className="col-span-6 text-xs uppercase tracking-widest font-bold">Institution</div>
                  <div className="col-span-1 text-xs uppercase tracking-widest font-bold">Nat</div>
                  <div className="col-span-2 text-xs uppercase tracking-widest font-bold">Log</div>
                  <div className="col-span-2 text-xs uppercase tracking-widest font-bold">Str</div>
                </div>
                {getSortedSchools().map((school) => (
                  <div 
                    key={school.rank} 
                    className="grid grid-cols-12 gap-4 p-6 hover:bg-gray-50 transition-colors cursor-pointer group"
                    onClick={() => setSelectedSchool(school.school)}
                  >
                    <div className="col-span-1 text-sm font-bold tabular-nums">
                      {String(school.rank).padStart(2, '0')}
                    </div>
                    <div className="col-span-6 text-sm group-hover:font-bold transition-all">{school.school}</div>
                    <div className="col-span-1 text-lg font-black tabular-nums">{school.nationalScore}</div>
                    <div className="col-span-2 text-sm tabular-nums">{school.logistics}</div>
                    <div className="col-span-2 text-sm tabular-nums">{school.strategy}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Job Feed */}
      <section id="data" className="border-b-2 border-black bg-white" data-section="jobs">
        <div className="max-w-[1400px] mx-auto px-6 sm:px-8 lg:px-12 py-20">
          <div className={`text-center mb-12 ${visibleSections.has('jobs') ? 'animate-fade-in-up' : 'opacity-0'}`}>
            <h2 className="text-4xl sm:text-5xl font-black tracking-tight mb-4">LIVE DATA FEED</h2>
            <p className="text-lg text-gray-600">Real-time job market intelligence</p>
          </div>

          <div className={visibleSections.has('jobs') ? 'animate-fade-in-scale' : 'opacity-0'} style={{ animationDelay: '0.2s' }}>
            <div className="bg-white border-2 border-black shadow-[8px_8px_0_0_rgba(0,0,0,1)] overflow-hidden">
              <div className="border-b-2 border-black p-6 bg-gray-50">
                <div className="flex items-center gap-3">
                  <TrendingUp className="w-5 h-5" />
                  <span className="text-sm font-bold tracking-wider uppercase">
                    Recent Job Postings
                  </span>
                </div>
              </div>

              {/* REPLACED CONTENT STARTS HERE */}
              <div className="divide-y-2 divide-black max-h-[600px] overflow-y-auto">
                {realJobsData.slice(0, 50).map((job, idx) => (
                  <div 
                    key={idx} 
                    className="grid grid-cols-12 gap-4 p-6 hover:bg-gray-50 transition-colors group cursor-default"
                  >
                    {/* Job Title & Description */}
                    <div className="col-span-12 md:col-span-6">
                      <div className="text-sm font-black group-hover:text-blue-600 transition-colors">
                        {job.job_title_actual}
                      </div>
                      <div className="text-xs text-gray-500 mt-1 line-clamp-2">
                        {job.description}
                      </div>
                    </div>

                    {/* Company Name */}
                    <div className="col-span-6 md:col-span-4 flex items-center">
                        <span className="text-sm font-bold bg-black text-white px-2 py-1 text-xs uppercase tracking-wider">
                            {job.company}
                        </span>
                    </div>

                    {/* Date & Location */}
                    <div className="col-span-6 md:col-span-2 text-right">
                      <div className="text-xs uppercase tracking-wider font-bold text-gray-600">
                        {job.date_collected}
                      </div>
                      <div className="text-[10px] text-gray-400 font-bold mt-1 uppercase">
                        {job.location_searched}
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <div className="border-t-2 border-black p-4 bg-white">
                <div className="text-xs text-center uppercase tracking-widest font-bold text-gray-600">
                  {realJobsData.length} Records • Updated Daily
                </div>
              </div>
              {/* REPLACED CONTENT ENDS HERE */}
              
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}