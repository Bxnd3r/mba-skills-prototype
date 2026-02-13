import { useState, useEffect, useRef } from 'react';
import { Search, TrendingUp, BookOpen, Award, ArrowRight, ChevronLeft, ChevronRight, X } from 'lucide-react';
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer, Legend, Tooltip } from 'recharts';

// --- IMPORTS ---
import realJobsData from '../data/jobs.json';

// --- DYNAMIC IMPORTS ---
const schoolFiles = import.meta.glob('../data/schools/*.json', { eager: true });
const allSchoolsData = Object.values(schoolFiles).map((file: any) => file.default);

// --- MOCK DATA ---
const skillsData = [
  { skill: 'Decision-Making', school: 65, comparison: 85 },
  { skill: 'Human Capital', school: 72, comparison: 78 },
  { skill: 'Strategy & Innovation', school: 88, comparison: 82 },
  { skill: 'Task Environment', school: 58, comparison: 90 },
  { skill: 'Admin & Control', school: 45, comparison: 68 },
  { skill: 'Logistics & Tech', school: 38, comparison: 92 },
];

// Combine scraped schools with mock schools
const scrapedSchoolNames = allSchoolsData.map((s: any) => s.school_name);
const allSchoolNames = [
  ...scrapedSchoolNames,
  'Northwestern University Kellogg',
  'Harvard Business School',
  'Stanford Graduate School of Business',
  'MIT Sloan School of Management',
  'Wharton School (UPenn)',
].filter((value, index, self) => self.indexOf(value) === index);

const mockSchoolRankings = [
  { rank: 1, school: 'MIT Sloan School of Management', nationalScore: 94, logistics: 98, strategy: 92 },
  { rank: 2, school: 'Stanford Graduate School of Business', nationalScore: 92, logistics: 89, strategy: 96 },
  { rank: 3, school: 'Northwestern University Kellogg', nationalScore: 89, logistics: 85, strategy: 94 },
  { rank: 4, school: 'Harvard Business School', nationalScore: 88, logistics: 82, strategy: 93 },
  { rank: 5, school: 'Wharton School (UPenn)', nationalScore: 87, logistics: 84, strategy: 90 },
];

export default function HomePage() {
  // State
  const [selectedSchool, setSelectedSchool] = useState(allSchoolNames[0] || 'No Data');
  const [searchQuery, setSearchQuery] = useState('');
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  
  // View State
  const [currentSchoolIndex, setCurrentSchoolIndex] = useState(0);
  const [sortBy, setSortBy] = useState<string>('highest-national');
  const [visibleSections, setVisibleSections] = useState<Set<string>>(new Set());
  
  const radarRef = useRef<HTMLDivElement>(null);
  const searchContainerRef = useRef<HTMLDivElement>(null);

  // Derived Data
  const currentSchoolData = allSchoolsData.find((s: any) => s.school_name === selectedSchool) || {
    school_name: selectedSchool,
    curriculum: []
  };

  // Click Outside Handler for Search
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (searchContainerRef.current && !searchContainerRef.current.contains(event.target as Node)) {
        setShowSuggestions(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Intersection Observer for Animations
  useEffect(() => {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const id = entry.target.getAttribute('data-section');
          if (id) setVisibleSections((prev) => new Set([...prev, id]));
        }
      });
    }, { threshold: 0.15 });

    document.querySelectorAll('[data-section]').forEach((el) => observer.observe(el));
    return () => observer.disconnect();
  }, []);

  // Handlers
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const query = e.target.value;
    setSearchQuery(query);
    
    if (query.length > 0) {
      const filtered = allSchoolNames.filter(school => 
        school.toLowerCase().includes(query.toLowerCase())
      );
      setSuggestions(filtered);
      setShowSuggestions(true);
    } else {
      setShowSuggestions(false);
    }
  };

  const selectSchool = (schoolName: string) => {
    setSelectedSchool(schoolName);
    setSearchQuery('');
    setShowSuggestions(false);
    scrollToRadar();
  };

  const scrollToRadar = () => {
    radarRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const parseCourse = (courseString: string) => {
    const parts = courseString.split(':');
    if (parts.length > 1) {
        return { code: parts[0], name: parts.slice(1).join(':') };
    }
    return { code: '---', name: courseString };
  };

  return (
    <div className="min-h-screen bg-white">
      {/* HERO SECTION */}
      <section className="border-b-2 border-black min-h-[60vh] flex items-center justify-center py-20" data-section="hero">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <div className={`mb-6 ${visibleSections.has('hero') ? 'animate-fade-in-up' : 'opacity-0'}`}>
            <div className="inline-flex items-center gap-2 bg-black text-white px-3 py-1 text-xs font-bold tracking-widest uppercase rounded-full">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              System Online — {realJobsData.length} Jobs Tracked
            </div>
          </div>

          <h1 className={`text-4xl sm:text-6xl md:text-7xl font-black tracking-tighter leading-[0.9] mb-8 ${
            visibleSections.has('hero') ? 'animate-fade-in-scale' : 'opacity-0'
          }`} style={{ animationDelay: '0.2s' }}>
            COMPARE A<br/>
            BUSINESS SCHOOL<br/>
            TO THE MARKET
          </h1>

          <p className={`text-lg text-gray-600 mb-10 max-w-xl mx-auto leading-relaxed ${
            visibleSections.has('hero') ? 'animate-fade-in-up' : 'opacity-0'
          }`} style={{ animationDelay: '0.4s' }}>
            Real-time alignment analysis between MBA curricula and market demand.
          </p>

          <button
            onClick={scrollToRadar}
            className={`group inline-flex items-center gap-2 bg-black text-white px-8 py-4 text-sm font-bold tracking-wider uppercase hover:bg-gray-800 transition-all shadow-[4px_4px_0_0_rgba(0,0,0,1)] hover:shadow-none hover:translate-x-1 hover:translate-y-1 ${
              visibleSections.has('hero') ? 'animate-fade-in-scale' : 'opacity-0'
            }`}
            style={{ animationDelay: '0.6s' }}
          >
            Start Analysis
            <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </button>
        </div>
      </section>

      {/* RADAR CHART SECTION */}
      <section ref={radarRef} className="border-b-2 border-black bg-gray-50 py-16" data-section="radar">
        <div className="max-w-[1400px] mx-auto px-6 lg:px-12">
          <div className="grid lg:grid-cols-3 gap-8">
            
            {/* Main Chart Area */}
            <div className="lg:col-span-2">
              <div className={visibleSections.has('radar') ? 'animate-slide-in-left' : 'opacity-0'}>
                
                {/* SEARCH BAR WITH DROPDOWN */}
                <div className="mb-6 relative z-20" ref={searchContainerRef}>
                  <div className="bg-white border-2 border-black p-4 shadow-[4px_4px_0_0_rgba(0,0,0,1)]">
                    <label className="block text-xs font-bold tracking-wider uppercase mb-2 text-gray-500">
                      Search Institution
                    </label>
                    <div className="flex gap-2">
                      <div className="relative flex-1">
                        <input
                          type="text"
                          value={searchQuery}
                          onChange={handleSearchChange}
                          onFocus={() => searchQuery && setShowSuggestions(true)}
                          placeholder="Type a school name (e.g. Harvard)..."
                          className="w-full border-2 border-gray-200 px-4 py-2 text-sm bg-gray-50 focus:outline-none focus:border-black transition-colors font-medium"
                        />
                        {/* SUGGESTIONS DROPDOWN */}
                        {showSuggestions && (
                          <div className="absolute top-full left-0 right-0 bg-white border-2 border-black border-t-0 max-h-60 overflow-y-auto shadow-lg mt-1">
                            {suggestions.length > 0 ? (
                              suggestions.map((school, idx) => (
                                <button
                                  key={idx}
                                  onClick={() => selectSchool(school)}
                                  className="w-full text-left px-4 py-3 text-sm hover:bg-gray-100 border-b border-gray-100 last:border-0 font-medium"
                                >
                                  {school}
                                </button>
                              ))
                            ) : (
                              <div className="px-4 py-3 text-sm text-gray-400 italic">No schools found</div>
                            )}
                          </div>
                        )}
                      </div>
                      <button className="bg-black text-white px-4 py-2 hover:bg-gray-800 transition-colors">
                        <Search className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>

                {/* Radar Chart */}
                <div className="bg-white border-2 border-black shadow-[8px_8px_0_0_rgba(0,0,0,1)] overflow-hidden">
                  <div className="border-b-2 border-black p-4 bg-gray-50 flex justify-between items-center">
                    <h2 className="text-xl font-black tracking-tight">{selectedSchool}</h2>
                  </div>
                  <div className="p-4 h-[400px] bg-white">
                    <ResponsiveContainer width="100%" height="100%">
                      <RadarChart cx="50%" cy="50%" outerRadius="70%" data={skillsData}>
                        <PolarGrid />
                        <PolarAngleAxis dataKey="skill" tick={{ fontSize: 10, fontWeight: 'bold' }} />
                        <PolarRadiusAxis angle={30} domain={[0, 100]} />
                        <Radar name="School Score" dataKey="school" stroke="#000000" fill="#000000" fillOpacity={0.1} />
                        <Radar name="Market Demand" dataKey="comparison" stroke="#ff0000" fill="#ff0000" fillOpacity={0.1} />
                        <Legend />
                        <Tooltip />
                      </RadarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>
            </div>

            {/* Sidebar Stats */}
            <div className="lg:col-span-1">
              <div className={`bg-white border-2 border-black shadow-[8px_8px_0_0_rgba(0,0,0,1)] ${visibleSections.has('radar') ? 'animate-slide-in-right' : 'opacity-0'}`}>
                <div className="border-b-2 border-black p-4 bg-gray-50">
                  <h3 className="text-sm font-black tracking-tight uppercase">Analysis Controls</h3>
                </div>
                <div className="p-4 space-y-2">
                  {['Local Job Market', 'National Job Market', 'Peer Comparison'].map((label, idx) => (
                    <button key={idx} className="w-full text-left px-4 py-3 border-2 border-gray-200 text-xs font-bold uppercase hover:border-black hover:bg-gray-50 transition-all">
                      {label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* COURSE CATALOG */}
      <section className="border-b-2 border-black bg-white py-16" data-section="courses">
        <div className="max-w-[1400px] mx-auto px-6 lg:px-12">
          <div className="mb-8 text-center">
            <h2 className="text-3xl font-black tracking-tight mb-2">CURRICULUM</h2>
            <p className="text-gray-500 text-sm">
              {currentSchoolData.school_name} — {currentSchoolData.curriculum?.length || 0} Courses Found
            </p>
          </div>

          <div className="bg-white border-2 border-black shadow-[8px_8px_0_0_rgba(0,0,0,1)]">
            <div className="max-h-[500px] overflow-y-auto divide-y-2 divide-gray-100">
              {currentSchoolData.curriculum && currentSchoolData.curriculum.length > 0 ? (
                currentSchoolData.curriculum.map((course: any, idx: number) => {
                  const { code, name } = parseCourse(course.course);
                  return (
                    <div key={idx} className="p-4 hover:bg-gray-50 grid grid-cols-12 gap-4">
                      <div className="col-span-3 sm:col-span-2 text-xs font-bold text-gray-400">{code}</div>
                      <div className="col-span-9 sm:col-span-7 text-sm font-bold text-blue-900">{name}</div>
                      <div className="col-span-12 sm:col-span-3 text-xs text-gray-500 line-clamp-1">{course.description}</div>
                    </div>
                  );
                })
              ) : (
                <div className="p-8 text-center text-gray-400 text-sm">
                  No curriculum data available. Use the scraper to add data for this school.
                </div>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* LIVE JOB FEED */}
      <section id="data" className="border-b-2 border-black bg-gray-50 py-16" data-section="jobs">
        <div className="max-w-[1400px] mx-auto px-6 lg:px-12">
          <div className="mb-8 text-center">
            <h2 className="text-3xl font-black tracking-tight mb-2">LIVE MARKET FEED</h2>
            <p className="text-gray-500 text-sm">Real-time data from {realJobsData.length} active listings</p>
          </div>

          <div className="bg-white border-2 border-black shadow-[8px_8px_0_0_rgba(0,0,0,1)]">
            <div className="border-b-2 border-black p-4 bg-gray-50 flex items-center gap-2">
              <TrendingUp className="w-4 h-4" />
              <span className="text-xs font-bold uppercase tracking-wider">Recent Postings</span>
            </div>

            <div className="max-h-[600px] overflow-y-auto divide-y-2 divide-black">
              {realJobsData && realJobsData.length > 0 ? (
                realJobsData.slice(0, 100).map((job, idx) => (
                  <div key={idx} className="p-6 hover:bg-blue-50 transition-colors group">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <h4 className="text-sm font-black text-gray-900 group-hover:text-blue-700">{job.job_title_actual}</h4>
                        <span className="text-xs font-bold text-gray-500 uppercase">{job.company}</span>
                      </div>
                      <div className="text-right">
                        <div className="text-xs font-bold text-gray-400">{job.date_collected}</div>
                        <div className="text-[10px] text-gray-400 uppercase mt-1">{job.location_searched}</div>
                      </div>
                    </div>
                    <p className="text-xs text-gray-600 line-clamp-2 leading-relaxed">
                      {job.description}
                    </p>
                  </div>
                ))
              ) : (
                <div className="p-12 text-center">
                  <p className="text-red-500 font-bold">No Job Data Found</p>
                  <p className="text-xs text-gray-500 mt-2">Please ensure src/data/jobs.json contains valid data.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}