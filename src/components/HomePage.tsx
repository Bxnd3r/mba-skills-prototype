import { useState, useEffect, useRef } from 'react';
import { Search, TrendingUp, BookOpen, Award, ArrowRight, ChevronRight, X } from 'lucide-react';
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

// Helper to clean names (Issue #5: Remove Underscores)
const cleanName = (name: string) => {
  if (!name) return "";
  return name.replace(/_/g, ' ');
};

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

export default function HomePage() {
  // State: Default to NULL (Issue #1: Site rests on blank state)
  const [selectedSchool, setSelectedSchool] = useState<string | null>(null);
  
  const [searchQuery, setSearchQuery] = useState('');
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [visibleSections, setVisibleSections] = useState<Set<string>>(new Set());
  
  const radarRef = useRef<HTMLDivElement>(null);
  const searchContainerRef = useRef<HTMLDivElement>(null);

  // Derived Data
  const currentSchoolData = selectedSchool 
    ? allSchoolsData.find((s: any) => s.school_name === selectedSchool) || { school_name: selectedSchool, curriculum: [] }
    : null;

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

  // Intersection Observer
  useEffect(() => {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const id = entry.target.getAttribute('data-section');
          if (id) setVisibleSections((prev) => new Set([...prev, id]));
        }
      });
    }, { threshold: 0.1 });

    document.querySelectorAll('[data-section]').forEach((el) => observer.observe(el));
    return () => observer.disconnect();
  }, []);

  // Handlers
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const query = e.target.value;
    setSearchQuery(query);
    
    if (query.length > 0) {
      const filtered = allSchoolNames.filter(school => 
        cleanName(school).toLowerCase().includes(cleanName(query).toLowerCase())
      );
      setSuggestions(filtered);
      setShowSuggestions(true);
    } else {
      setShowSuggestions(false);
    }
  };

  const selectSchool = (schoolName: string) => {
    setSelectedSchool(schoolName);
    setSearchQuery(cleanName(schoolName)); // Show clean name in box
    setShowSuggestions(false);
    
    // Smooth scroll to data after selection
    setTimeout(() => {
        radarRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
  };

  const parseCourse = (courseString: string) => {
    const parts = courseString.split(':');
    if (parts.length > 1) {
        return { code: parts[0], name: parts.slice(1).join(':') };
    }
    return { code: '---', name: courseString };
  };

  return (
    <div className="min-h-screen bg-white font-sans text-slate-900">
      
      {/* HERO SECTION */}
      <section className="border-b-2 border-black min-h-[70vh] flex flex-col items-center justify-center py-20 bg-white relative" data-section="hero">
        <div className="max-w-4xl w-full px-6 text-center z-10">
          
          {/* Status Badge */}
          <div className={`mb-8 flex justify-center ${visibleSections.has('hero') ? 'animate-fade-in-up' : 'opacity-0'}`}>
            <div className="inline-flex items-center gap-3 bg-black text-white px-4 py-2 text-xs font-bold tracking-widest uppercase rounded-full shadow-lg">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              System Online — {realJobsData.length} Jobs Tracked
            </div>
          </div>

          <h1 className={`text-5xl sm:text-7xl font-black tracking-tighter leading-[0.9] mb-8 ${
            visibleSections.has('hero') ? 'animate-fade-in-scale' : 'opacity-0'
          }`} style={{ animationDelay: '0.2s' }}>
            COMPARE A<br/>
            BUSINESS SCHOOL<br/>
            TO THE MARKET
          </h1>

          <p className={`text-xl text-gray-600 mb-12 max-w-xl mx-auto leading-relaxed font-medium ${
            visibleSections.has('hero') ? 'animate-fade-in-up' : 'opacity-0'
          }`} style={{ animationDelay: '0.4s' }}>
            Real-time alignment analysis between MBA curricula and market demand.
          </p>

          {/* MAIN SEARCH BAR (Always Visible) */}
          <div className={`max-w-xl mx-auto relative ${visibleSections.has('hero') ? 'animate-fade-in-up' : 'opacity-0'}`} style={{ animationDelay: '0.5s' }} ref={searchContainerRef}>
            <div className="relative group">
                <div className="absolute inset-0 bg-black translate-x-1 translate-y-1 rounded-lg transition-transform group-hover:translate-x-2 group-hover:translate-y-2"></div>
                <div className="relative bg-white border-2 border-black rounded-lg flex items-center p-2">
                    <Search className="w-6 h-6 ml-3 text-gray-400" />
                    <input
                        type="text"
                        value={searchQuery}
                        onChange={handleSearchChange}
                        onFocus={() => searchQuery && setShowSuggestions(true)}
                        placeholder="Search for a university..."
                        className="w-full h-12 px-4 text-lg font-bold outline-none placeholder:font-normal placeholder:text-gray-300"
                    />
                    {selectedSchool && (
                        <button onClick={() => {setSelectedSchool(null); setSearchQuery('');}} className="p-2 hover:bg-gray-100 rounded-full">
                            <X className="w-5 h-5 text-gray-500"/>
                        </button>
                    )}
                </div>
            </div>

            {/* Suggestions Dropdown */}
            {showSuggestions && (
                <div className="absolute top-full left-0 right-0 mt-2 bg-white border-2 border-black rounded-lg shadow-xl max-h-80 overflow-y-auto z-50 divide-y divide-gray-100">
                {suggestions.length > 0 ? (
                    suggestions.map((school, idx) => (
                    <button
                        key={idx}
                        onClick={() => selectSchool(school)}
                        className="w-full text-left px-6 py-4 text-sm font-bold hover:bg-blue-50 transition-colors flex justify-between items-center group"
                    >
                        {cleanName(school)}
                        <ChevronRight className="w-4 h-4 text-gray-300 group-hover:text-blue-600" />
                    </button>
                    ))
                ) : (
                    <div className="px-6 py-4 text-sm text-gray-400 italic">No schools found</div>
                )}
                </div>
            )}
          </div>

        </div>
      </section>

      {/* CONDITIONAL CONTENT: Only show if a school is selected */}
      {selectedSchool ? (
        <div ref={radarRef}>
            
            {/* SCHOOL HEADER */}
            <div className="bg-black text-white py-12">
                <div className="max-w-[1400px] mx-auto px-6 text-center">
                    <h2 className="text-3xl font-bold tracking-widest uppercase text-gray-400 mb-2">Analysis Report</h2>
                    <h3 className="text-4xl sm:text-6xl font-black tracking-tighter">{cleanName(selectedSchool)}</h3>
                </div>
            </div>

            <div className="max-w-[1600px] mx-auto px-6 lg:px-12 py-16 grid lg:grid-cols-12 gap-8">
                
                {/* LEFT COL: RADAR CHART (Fixed) */}
                <div className="lg:col-span-4 space-y-8" data-section="radar">
                    <div className="bg-white border-2 border-black shadow-[8px_8px_0_0_rgba(0,0,0,1)] p-6">
                        <div className="mb-6 flex items-center justify-between">
                            <h3 className="font-black text-xl uppercase">Skill Gap Analysis</h3>
                            <Award className="w-6 h-6" />
                        </div>
                        <div className="h-[350px]">
                            <ResponsiveContainer width="100%" height="100%">
                                <RadarChart cx="50%" cy="50%" outerRadius="70%" data={skillsData}>
                                <PolarGrid />
                                <PolarAngleAxis dataKey="skill" tick={{ fontSize: 10, fontWeight: 'bold' }} />
                                <PolarRadiusAxis angle={30} domain={[0, 100]} />
                                <Radar name={cleanName(selectedSchool)} dataKey="school" stroke="#000000" fill="#000000" fillOpacity={0.1} />
                                <Radar name="Market Demand" dataKey="comparison" stroke="#ff0000" fill="#ff0000" fillOpacity={0.1} />
                                <Legend />
                                <Tooltip />
                                </RadarChart>
                            </ResponsiveContainer>
                        </div>
                    </div>

                    <div className="bg-gray-50 border-2 border-black p-6">
                        <h4 className="font-bold text-sm uppercase mb-4 text-gray-500">Quick Stats</h4>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="p-4 bg-white border border-gray-200">
                                <div className="text-2xl font-black">{currentSchoolData?.curriculum?.length || 0}</div>
                                <div className="text-xs text-gray-500 font-bold uppercase">Courses</div>
                            </div>
                            <div className="p-4 bg-white border border-gray-200">
                                <div className="text-2xl font-black">92%</div>
                                <div className="text-xs text-gray-500 font-bold uppercase">Alignment</div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* RIGHT COL: SCROLLABLE DATA WINDOWS (Issue #2 & #4) */}
                <div className="lg:col-span-8 grid md:grid-cols-2 gap-8">
                    
                    {/* CURRICULUM WINDOW */}
                    <div className="flex flex-col h-[500px] border-2 border-black shadow-[8px_8px_0_0_rgba(0,0,0,1)] bg-white">
                        <div className="p-4 border-b-2 border-black bg-gray-50 flex items-center justify-between">
                            <div className="flex items-center gap-2">
                                <BookOpen className="w-5 h-5" />
                                <span className="font-black text-sm uppercase tracking-wider">Curriculum Feed</span>
                            </div>
                            <span className="text-xs font-bold text-gray-400">{currentSchoolData?.curriculum?.length || 0} ITEMS</span>
                        </div>
                        
                        {/* Scrollable Area */}
                        <div className="flex-1 overflow-y-auto p-0">
                            {currentSchoolData?.curriculum && currentSchoolData.curriculum.length > 0 ? (
                                <div className="divide-y divide-gray-100">
                                    {currentSchoolData.curriculum.map((course: any, idx: number) => {
                                        const { code, name } = parseCourse(course.course);
                                        return (
                                            <div key={idx} className="p-5 hover:bg-blue-50 transition-colors group">
                                                {/* Row 1: Code & Title */}
                                                <div className="flex items-baseline justify-between mb-2">
                                                    <h4 className="text-sm font-bold text-blue-900 group-hover:underline">{name}</h4>
                                                    <span className="text-xs font-mono font-bold text-gray-400 bg-gray-100 px-2 py-1 rounded ml-4 whitespace-nowrap">{code}</span>
                                                </div>
                                                {/* Row 2: Full Width Description (Issue #4) */}
                                                <p className="text-xs text-gray-600 leading-relaxed">
                                                    {course.description}
                                                </p>
                                            </div>
                                        );
                                    })}
                                </div>
                            ) : (
                                <div className="h-full flex flex-col items-center justify-center text-gray-400 p-8 text-center">
                                    <BookOpen className="w-12 h-12 mb-4 opacity-20" />
                                    <p>No curriculum data found.</p>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* LIVE JOB FEED WINDOW (Issue #3) */}
                    <div className="flex flex-col h-[500px] border-2 border-black shadow-[8px_8px_0_0_rgba(0,0,0,1)] bg-white">
                        <div className="p-4 border-b-2 border-black bg-gray-50 flex items-center justify-between">
                            <div className="flex items-center gap-2">
                                <TrendingUp className="w-5 h-5" />
                                <span className="font-black text-sm uppercase tracking-wider">Live Job Market</span>
                            </div>
                            <span className="text-xs font-bold text-gray-400">{realJobsData.length} ACTIVE</span>
                        </div>

                        {/* Scrollable Area */}
                        <div className="flex-1 overflow-y-auto p-0">
                            {realJobsData && realJobsData.length > 0 ? (
                                <div className="divide-y divide-gray-100">
                                    {realJobsData.slice(0, 100).map((job, idx) => (
                                        <div key={idx} className="p-4 hover:bg-green-50 transition-colors flex items-center justify-between group">
                                            {/* JUST THE TITLE (Issue #3) */}
                                            <span className="text-sm font-bold text-gray-800 group-hover:text-green-700 truncate pr-4">
                                                {job.job_title_actual}
                                            </span>
                                            <ArrowRight className="w-4 h-4 text-gray-300 opacity-0 group-hover:opacity-100 transition-opacity" />
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="h-full flex flex-col items-center justify-center text-gray-400 p-8 text-center">
                                    <TrendingUp className="w-12 h-12 mb-4 opacity-20" />
                                    <p>No active job listings.</p>
                                </div>
                            )}
                        </div>
                    </div>

                </div>
            </div>
        </div>
      ) : (
        /* EMPTY STATE PLACEHOLDER (Issue #1) */
        <div className="py-20 bg-gray-50 border-t-2 border-black text-center text-gray-400">
            <p className="uppercase tracking-widest font-bold text-sm">Select a school above to begin analysis</p>
        </div>
      )}

    </div>
  );
}