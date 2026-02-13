import { useState, useEffect, useRef } from 'react';
import { Search, TrendingUp, BookOpen, Award, ArrowRight, ChevronRight, X } from 'lucide-react';
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer, Legend, Tooltip } from 'recharts';

// --- IMPORTS ---
import realJobsData from '../data/jobs.json';

// --- DYNAMIC IMPORTS ---
const schoolFiles = import.meta.glob('../data/schools/*.json', { eager: true });
const allSchoolsData = Object.values(schoolFiles).map((file: any) => file.default);

// --- MOCK DATA FOR CHARTS ---
const skillsData = [
  { skill: 'Decision-Making', school: 65, comparison: 85 },
  { skill: 'Human Capital', school: 72, comparison: 78 },
  { skill: 'Strategy & Innovation', school: 88, comparison: 82 },
  { skill: 'Task Environment', school: 58, comparison: 90 },
  { skill: 'Admin & Control', school: 45, comparison: 68 },
  { skill: 'Logistics & Tech', school: 38, comparison: 92 },
];

// Helper: Remove underscores from names (e.g. "The_University_of_Chicago")
const cleanName = (name: string) => {
  if (!name) return "";
  return name.replace(/_/g, ' ');
};

// Combine scraped schools with mock schools for the search list
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
  // --- STATE ---
  const [selectedSchool, setSelectedSchool] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  
  // Animation State
  const [visibleSections, setVisibleSections] = useState<Set<string>>(new Set());
  
  // Refs for scrolling and click detection
  const dashboardRef = useRef<HTMLDivElement>(null);
  const searchContainerRef = useRef<HTMLDivElement>(null);

  // Derived Data (Get the data for the selected school)
  const currentSchoolData = selectedSchool 
    ? allSchoolsData.find((s: any) => s.school_name === selectedSchool) || { school_name: selectedSchool, curriculum: [] }
    : null;

  // --- EFFECTS ---

  // Handle clicking outside the search box to close dropdown
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (searchContainerRef.current && !searchContainerRef.current.contains(event.target as Node)) {
        setShowSuggestions(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Fade-in animations
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

  // --- HANDLERS ---

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const query = e.target.value;
    setSearchQuery(query);
    
    if (query.length > 0) {
      // Fuzzy search + clean names
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
    setSearchQuery(cleanName(schoolName)); // Put clean name in box
    setShowSuggestions(false);
    
    // Scroll down to the dashboard
    setTimeout(() => {
        dashboardRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
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
      <section className="border-b-2 border-black min-h-[60vh] flex flex-col items-center justify-center py-20 relative bg-white" data-section="hero">
        <div className="max-w-4xl w-full px-6 text-center z-10">
          
          <div className={`mb-8 flex justify-center ${visibleSections.has('hero') ? 'animate-fade-in-up' : 'opacity-0'}`}>
            <div className="inline-flex items-center gap-3 bg-black text-white px-4 py-2 text-xs font-bold tracking-widest uppercase rounded-full shadow-lg">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              Live Data — {realJobsData.length} Jobs Tracked
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

          {/* SEARCH BAR CONTAINER */}
          <div 
            className={`max-w-xl mx-auto relative ${visibleSections.has('hero') ? 'animate-fade-in-up' : 'opacity-0'}`} 
            style={{ animationDelay: '0.5s' }} 
            ref={searchContainerRef}
          >
            <div className="relative group">
                {/* Shadow block */}
                <div className="absolute inset-0 bg-black translate-x-2 translate-y-2 rounded-lg transition-transform group-hover:translate-x-3 group-hover:translate-y-3"></div>
                
                {/* Input block */}
                <div className="relative bg-white border-2 border-black rounded-lg flex items-center p-1 z-20">
                    <Search className="w-6 h-6 ml-3 text-gray-400" />
                    <input
                        type="text"
                        value={searchQuery}
                        onChange={handleSearchChange}
                        onFocus={() => searchQuery && setShowSuggestions(true)}
                        placeholder="Search for a university..."
                        className="w-full h-12 px-4 text-lg font-bold outline-none placeholder:font-normal placeholder:text-gray-300 rounded-lg"
                    />
                    {selectedSchool && (
                        <button onClick={() => {setSelectedSchool(null); setSearchQuery('');}} className="p-2 hover:bg-gray-100 rounded-full mr-1">
                            <X className="w-5 h-5 text-gray-500"/>
                        </button>
                    )}
                </div>
            </div>

            {/* SUGGESTIONS DROPDOWN (Fixed: Absolute position + Max Height) */}
            {showSuggestions && (
                <div className="absolute top-full left-0 right-0 mt-3 bg-white border-2 border-black rounded-lg shadow-xl max-h-60 overflow-y-auto z-50 divide-y divide-gray-100">
                {suggestions.length > 0 ? (
                    suggestions.map((school, idx) => (
                    <button
                        key={idx}
                        onClick={() => selectSchool(school)}
                        className="w-full text-left px-6 py-3 text-sm font-bold hover:bg-blue-50 transition-colors flex justify-between items-center group"
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

      {/* DASHBOARD SECTION (Only visible when school selected) */}
      {selectedSchool ? (
        <div ref={dashboardRef} className="bg-gray-50 border-t-2 border-black min-h-screen">
            
            {/* SCHOOL HEADER */}
            <div className="bg-white border-b-2 border-black py-10">
                <div className="max-w-[1400px] mx-auto px-6 text-center">
                    <h2 className="text-sm font-bold tracking-widest uppercase text-gray-400 mb-2">Analysis Report</h2>
                    <h3 className="text-3xl sm:text-5xl font-black tracking-tighter">{cleanName(selectedSchool)}</h3>
                </div>
            </div>

            <div className="max-w-[1600px] mx-auto px-6 lg:px-12 py-12">
                <div className="grid lg:grid-cols-12 gap-8">
                
                    {/* LEFT COLUMN: RADAR CHART */}
                    <div className="lg:col-span-5 space-y-6" data-section="radar">
                        <div className="bg-white border-2 border-black shadow-[8px_8px_0_0_rgba(0,0,0,1)] p-6">
                            <div className="mb-4 flex items-center justify-between border-b-2 border-gray-100 pb-4">
                                <h3 className="font-black text-lg uppercase flex items-center gap-2">
                                    <Award className="w-5 h-5" />
                                    Skill Gap Analysis
                                </h3>
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

                        {/* Quick Stats */}
                        <div className="grid grid-cols-2 gap-4">
                            <div className="p-6 bg-white border-2 border-black shadow-[4px_4px_0_0_rgba(0,0,0,1)]">
                                <div className="text-3xl font-black">{currentSchoolData?.curriculum?.length || 0}</div>
                                <div className="text-xs text-gray-500 font-bold uppercase mt-1">Total Courses</div>
                            </div>
                            <div className="p-6 bg-white border-2 border-black shadow-[4px_4px_0_0_rgba(0,0,0,1)]">
                                <div className="text-3xl font-black">{realJobsData.length}</div>
                                <div className="text-xs text-gray-500 font-bold uppercase mt-1">Jobs Analyzed</div>
                            </div>
                        </div>
                    </div>

                    {/* RIGHT COLUMN: DATA WINDOWS (Stacked) */}
                    <div className="lg:col-span-7 space-y-8">
                        
                        {/* 1. CURRICULUM WINDOW (Fixed Height + Scroll) */}
                        <div className="bg-white border-2 border-black shadow-[8px_8px_0_0_rgba(0,0,0,1)] flex flex-col">
                            <div className="p-4 border-b-2 border-black bg-gray-50 flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                    <BookOpen className="w-5 h-5" />
                                    <span className="font-black text-sm uppercase tracking-wider">Curriculum Feed</span>
                                </div>
                                <span className="text-xs font-bold bg-black text-white px-2 py-1 rounded">SCROLL TO VIEW</span>
                            </div>
                            
                            {/* MINI WINDOW CONTAINER: h-80 (320px) */}
                            <div className="h-80 overflow-y-auto p-0 scrollbar-thin">
                                {currentSchoolData?.curriculum && currentSchoolData.curriculum.length > 0 ? (
                                    <div className="divide-y divide-gray-100">
                                        {currentSchoolData.curriculum.map((course: any, idx: number) => {
                                            const { code, name } = parseCourse(course.course);
                                            return (
                                                <div key={idx} className="p-5 hover:bg-blue-50 transition-colors">
                                                    <div className="flex items-baseline justify-between mb-1">
                                                        <h4 className="text-sm font-bold text-blue-900">{name}</h4>
                                                        <span className="text-xs font-mono font-bold text-gray-400 bg-gray-100 px-2 py-1 ml-4 whitespace-nowrap">{code}</span>
                                                    </div>
                                                    <p className="text-xs text-gray-500 leading-relaxed block w-full">
                                                        {course.description}
                                                    </p>
                                                </div>
                                            );
                                        })}
                                    </div>
                                ) : (
                                    <div className="h-full flex flex-col items-center justify-center text-gray-400">
                                        <p>No curriculum data found.</p>
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* 2. JOBS WINDOW (Fixed Height + Scroll) */}
                        <div className="bg-white border-2 border-black shadow-[8px_8px_0_0_rgba(0,0,0,1)] flex flex-col">
                            <div className="p-4 border-b-2 border-black bg-gray-50 flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                    <TrendingUp className="w-5 h-5" />
                                    <span className="font-black text-sm uppercase tracking-wider">Live Job Feed</span>
                                </div>
                                <span className="text-xs font-bold bg-green-100 text-green-800 px-2 py-1 rounded">LIVE</span>
                            </div>

                            {/* MINI WINDOW CONTAINER: h-80 (320px) */}
                            <div className="h-80 overflow-y-auto p-0 scrollbar-thin">
                                {realJobsData && realJobsData.length > 0 ? (
                                    <div className="divide-y divide-gray-100">
                                        {realJobsData.slice(0, 100).map((job, idx) => (
                                            <div key={idx} className="p-4 hover:bg-green-50 transition-colors flex items-center justify-between group">
                                                <span className="text-sm font-bold text-gray-800 group-hover:text-green-700 truncate pr-4">
                                                    {job.job_title_actual}
                                                </span>
                                                <ArrowRight className="w-4 h-4 text-gray-300 opacity-0 group-hover:opacity-100 transition-opacity" />
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <div className="h-full flex flex-col items-center justify-center text-gray-400">
                                        <p>No active job listings.</p>
                                    </div>
                                )}
                            </div>
                        </div>

                    </div>
                </div>
            </div>
        </div>
      ) : (
        /* NEUTRAL STATE (Empty Space) */
        <div className="h-40 bg-white"></div>
      )}
    </div>
  );
}