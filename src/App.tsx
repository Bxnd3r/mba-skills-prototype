import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { useState } from 'react';
import { Menu, X, Home, FileText, Award, Database } from 'lucide-react';
import HomePage from './components/HomePage';
import HowItWorks from './components/HowItWorks';

export default function App() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <Router>
      <div className="min-h-screen bg-white">
        {/* Navigation */}
        <nav className="border-b-2 border-black fixed top-0 left-0 right-0 z-50 bg-white">
          <div className="max-w-[1400px] mx-auto px-6 sm:px-8 lg:px-12">
            <div className="flex justify-between items-center h-20">
              <Link to="/" className="text-2xl font-black tracking-tight hover:scale-105 transition-transform">
                THE MBA<br/>SKILLS INDEX
              </Link>
              
              {/* Desktop Navigation */}
              <div className="hidden md:flex gap-8 items-center">
                <Link 
                  to="/" 
                  className="flex items-center gap-2 text-sm font-bold tracking-wider uppercase text-black hover:text-red-600 transition-colors relative group"
                >
                  <Home className="w-4 h-4" />
                  Home
                  <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-red-600 group-hover:w-full transition-all"></span>
                </Link>
                <Link 
                  to="/how-it-works" 
                  className="flex items-center gap-2 text-sm font-bold tracking-wider uppercase text-black hover:text-blue-600 transition-colors relative group"
                >
                  <FileText className="w-4 h-4" />
                  Methodology
                  <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-blue-600 group-hover:w-full transition-all"></span>
                </Link>
                <a 
                  href="#rankings"
                  className="flex items-center gap-2 text-sm font-bold tracking-wider uppercase text-black hover:text-purple-600 transition-colors relative group"
                >
                  <Award className="w-4 h-4" />
                  Rankings
                  <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-purple-600 group-hover:w-full transition-all"></span>
                </a>
                <a 
                  href="#data"
                  className="flex items-center gap-2 text-sm font-bold tracking-wider uppercase text-black hover:text-green-600 transition-colors relative group"
                >
                  <Database className="w-4 h-4" />
                  Live Data
                  <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-green-600 group-hover:w-full transition-all"></span>
                </a>
              </div>

              {/* Hamburger Menu Button */}
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="md:hidden p-2 hover:bg-gray-100 transition-colors"
              >
                {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
              </button>
            </div>

            {/* Mobile Menu */}
            {mobileMenuOpen && (
              <div className="md:hidden border-t-2 border-black py-4 animate-fade-in-up">
                <div className="flex flex-col gap-4">
                  <Link 
                    to="/" 
                    onClick={() => setMobileMenuOpen(false)}
                    className="flex items-center gap-2 text-sm font-bold tracking-wider uppercase text-black hover:text-red-600 transition-colors py-2"
                  >
                    <Home className="w-4 h-4" />
                    Home
                  </Link>
                  <Link 
                    to="/how-it-works" 
                    onClick={() => setMobileMenuOpen(false)}
                    className="flex items-center gap-2 text-sm font-bold tracking-wider uppercase text-black hover:text-blue-600 transition-colors py-2"
                  >
                    <FileText className="w-4 h-4" />
                    Methodology
                  </Link>
                  <a 
                    href="#rankings"
                    onClick={() => setMobileMenuOpen(false)}
                    className="flex items-center gap-2 text-sm font-bold tracking-wider uppercase text-black hover:text-purple-600 transition-colors py-2"
                  >
                    <Award className="w-4 h-4" />
                    Rankings
                  </a>
                  <a 
                    href="#data"
                    onClick={() => setMobileMenuOpen(false)}
                    className="flex items-center gap-2 text-sm font-bold tracking-wider uppercase text-black hover:text-green-600 transition-colors py-2"
                  >
                    <Database className="w-4 h-4" />
                    Live Data
                  </a>
                </div>
              </div>
            )}
          </div>
        </nav>

        {/* Main Content */}
        <div className="pt-20">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/how-it-works" element={<HowItWorks />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}
