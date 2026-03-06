"use client";

import { useState, useEffect } from "react";
import Sidebar from "@/components/Sidebar";
import { motion, AnimatePresence } from "framer-motion";
import ReactMarkdown from "react-markdown";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import "katex/dist/katex.min.css";
import { BookOpen, Lightbulb, Sparkles, ChevronRight, FileText } from "lucide-react";

export default function Home() {
  const [solutions, setSolutions] = useState<string[]>([]);
  const [pdfs, setPdfs] = useState<string[]>([]);
  const [selectedSolution, setSelectedSolution] = useState<string | null>(null);
  const [selectedPdf, setSelectedPdf] = useState<string | null>(null);
  const [solutionContent, setSolutionContent] = useState<string>("");
  const [activeTab, setActiveTab] = useState<"viewer" | "generator">("viewer");
  const [generatedContent, setGeneratedContent] = useState<string>("");
  const [generatedList, setGeneratedList] = useState<any[]>([]);
  const [selectedGeneratedId, setSelectedGeneratedId] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [constraints, setConstraints] = useState<string>("");

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = () => {
    fetch("http://localhost:8000/api/solutions")
      .then((res) => res.json())
      .then(setSolutions);
    fetch("http://localhost:8000/api/pdfs")
      .then((res) => res.json())
      .then(setPdfs);
    fetch("http://localhost:8000/api/generated_problems")
      .then((res) => res.json())
      .then(setGeneratedList);
  };

  const handleSelectSolution = async (filename: string) => {
    setIsLoading(true);
    setSelectedSolution(filename);
    setActiveTab("viewer"); // Auto-switch to viewer
    try {
      const res = await fetch(`http://localhost:8000/api/solution/${filename}`);
      const data = await res.json();
      setSolutionContent(data.content);

      // Try to auto-select matching PDF if not selected
      const baseName = filename.replace("_solutions.md", "");
      const matchingPdf = pdfs.find(p => p.includes(baseName));
      if (matchingPdf && !selectedPdf) {
        setSelectedPdf(matchingPdf);
      }
    } catch (error) {
      console.error("Failed to fetch solution:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectGenerated = async (id: number) => {
    setIsLoading(true);
    setSelectedGeneratedId(id);
    setActiveTab("generator");
    try {
      const res = await fetch(`http://localhost:8000/api/generated_problem/${id}`);
      const data = await res.json();

      // Reconstruct the full markdown view
      let markdown = `
### [Problem (${data.difficulty})]
${data.content}

**[Fusion Mapping]**
${data.fusion_mapping}

**[Step-by-Step Solution]**
${data.solution}

**[Final Answer]**
${data.answer}

**[Integrity Verification]**
${data.integrity_verification}
`;
      markdown = markdown.replace(/\\\\/g, '\\').replace(/\\n/g, '\n').replace(/\\lim_\{/g, '\\lim\\limits_{');
      setGeneratedContent(markdown);
    } catch (error) {
      console.error("Failed to fetch generated problem:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerate = async () => {
    setIsLoading(true);
    setGeneratedContent(""); // Clear current content
    setSelectedGeneratedId(null); // Clear selected history
    try {
      const response = await fetch("http://localhost:8000/api/stream/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ constraints })
      });

      if (!response.body) return;
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let done = false;

      setActiveTab("generator");

      while (!done) {
        const { value, done: doneReading } = await reader.read();
        done = doneReading;
        const chunkValue = decoder.decode(value, { stream: true });
        setGeneratedContent((prev) => (prev + chunkValue).replace(/\\lim_\{/g, '\\lim\\limits_{'));
      }
      fetchData(); // Refresh history list
    } catch (error) {
      console.error("Failed to generate:", error);
    } finally {
      setIsLoading(false);
    }
  };
  const handleSyncDB = async () => {
    setIsLoading(true);
    try {
      const response = await fetch("http://localhost:8000/api/sync_generated", {
        method: "POST"
      });
      const data = await response.json();
      if (data.success) {
        alert("DB 동기화 완료: " + data.message);
        fetchData(); // Refresh history list
      } else {
        alert("DB 동기화 실패: " + data.error);
      }
    } catch (error) {
      console.error("Failed to sync DB:", error);
      alert("DB 동기화 중 오류가 발생했습니다.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSolve = async () => {
    if (!selectedPdf) return;
    setIsAnalyzing(true);
    setSolutionContent(""); // Clear current content to show streaming
    try {
      const response = await fetch("http://localhost:8000/api/stream/solve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filename: selectedPdf })
      });

      if (!response.body) return;
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let done = false;

      while (!done) {
        const { value, done: doneReading } = await reader.read();
        done = doneReading;
        const chunkValue = decoder.decode(value, { stream: true });
        setSolutionContent((prev) => (prev + chunkValue).replace(/\\lim_\{/g, '\\lim\\limits_{'));
      }

      fetchData(); // Refresh list to see the new .md file
    } catch (error) {
      console.error("Analysis failed:", error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <main style={{ display: "flex", height: "100vh", width: "100vw" }}>
      <Sidebar
        solutions={solutions}
        pdfs={pdfs}
        generatedList={generatedList}
        selectedSolution={selectedSolution}
        selectedPdf={selectedPdf}
        selectedGeneratedId={selectedGeneratedId}
        onSelectSolution={handleSelectSolution}
        onSelectPdf={setSelectedPdf}
        onSelectGenerated={handleSelectGenerated}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
      />

      <section style={{ flex: 1, padding: "2rem", overflowY: "auto", position: "relative" }}>
        {/* Header Area */}
        <header style={{ marginBottom: "2rem", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <h1 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: "0.5rem" }}>
              {activeTab === "viewer" ? "문제 탐색기" : "AI 융합 문항 생성"}
            </h1>
            <p style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>
              {activeTab === "viewer" ? "원본 PDF와 AI 해설을 나란히 비교하며 학습하세요." : "기존 기출의 핵심 로직을 분석하여 탄생한 완전히 새로운 문제들입니다."}
            </p>
          </div>

          <div style={{ display: "flex", gap: "1rem" }}>
            {activeTab === "viewer" && selectedPdf && (
              <button
                onClick={handleSolve}
                disabled={isAnalyzing}
                className="glass"
                style={{ padding: "0.6rem 1.2rem", borderRadius: "8px", border: "1px solid var(--secondary)", color: "var(--secondary)", display: "flex", alignItems: "center", gap: "0.5rem", cursor: "pointer" }}
              >
                {isAnalyzing ? (
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                    style={{ width: "16px", height: "16px", border: "2px solid var(--secondary)", borderTopColor: "transparent", borderRadius: "50%" }}
                  />
                ) : <ChevronRight size={18} />}
                {isAnalyzing ? "분석 프로세스 가동 중..." : "선택한 PDF 분석 시작"}
              </button>
            )}

            {activeTab === "viewer" ? (
              <button
                onClick={() => setActiveTab("generator")}
                className="glass"
                style={{ padding: "0.6rem 1.2rem", borderRadius: "8px", border: "1px solid var(--primary)", color: "var(--primary)", display: "flex", alignItems: "center", gap: "0.5rem", cursor: "pointer" }}
              >
                <Sparkles size={18} />
                AI 문제 생성기로 이동
              </button>
            ) : (
              <div style={{ display: "flex", gap: "0.5rem" }}>
                <button
                  onClick={handleSyncDB}
                  disabled={isLoading}
                  className="glass"
                  style={{ padding: "0.6rem 1.2rem", borderRadius: "8px", border: "1px solid var(--secondary)", color: "var(--secondary)", display: "flex", alignItems: "center", gap: "0.5rem", cursor: "pointer" }}
                >
                  <FileText size={18} />
                  현재 MD파일을 DB에 추가
                </button>
                <button
                  onClick={handleGenerate}
                  disabled={isLoading}
                  className="glass"
                  style={{ padding: "0.6rem 1.2rem", borderRadius: "8px", border: "1px solid var(--primary)", color: "var(--primary)", display: "flex", alignItems: "center", gap: "0.5rem", cursor: "pointer" }}
                >
                  <Sparkles size={18} />
                  {isLoading ? "문항 생성 중..." : "새로운 문제 세트 만들기"}
                </button>
              </div>
            )}
          </div>
        </header>

        <AnimatePresence mode="wait">
          {activeTab === "viewer" ? (
            <motion.div
              key="viewer"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "2rem", height: "calc(100% - 6rem)" }}
            >
              {/* PDF Pane */}
              <div className="glass" style={{ borderRadius: "16px", overflow: "hidden", position: "relative" }}>
                <div style={{ padding: "1rem", borderBottom: "1px solid var(--glass-border)", display: "flex", alignItems: "center", gap: "0.5rem" }}>
                  <FileText size={18} color="var(--primary)" />
                  <span style={{ fontSize: "0.9rem", fontWeight: 500 }}>원본 PDF 문제지</span>
                </div>
                {selectedPdf ? (
                  <iframe
                    src={`http://localhost:8000/api/pdf/${selectedPdf}#toolbar=0`}
                    style={{ width: "100%", height: "calc(100% - 3.5rem)", border: "none" }}
                  />
                ) : (
                  <div style={{ height: "100%", display: "flex", alignItems: "center", justifyContent: "center", color: "var(--text-muted)" }}>
                    사이드바에서 분석할 PDF를 선택해 주세요
                  </div>
                )}
              </div>

              {/* Solution Pane */}
              <div className="glass" style={{ borderRadius: "16px", padding: "1.5rem", overflowY: "auto" }}>
                <div style={{ marginBottom: "1.5rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
                  <Lightbulb size={18} color="var(--secondary)" />
                  <span style={{ fontSize: "0.9rem", fontWeight: 500 }}>AI 해설 및 사고 과정</span>
                </div>

                {isLoading && !solutionContent ? (
                  <div style={{ height: "80%", display: "flex", alignItems: "center", justifyContent: "center" }}>
                    <div style={{ textAlign: "center" }}>
                      <motion.div
                        animate={{ rotate: 360 }}
                        transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                        style={{ width: "30px", height: "30px", border: "3px solid var(--primary)", borderTopColor: "transparent", borderRadius: "50%", margin: "0 auto 1rem" }}
                      />
                      <p style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>해설을 불러오는 중입니다...</p>
                    </div>
                  </div>
                ) : isAnalyzing && !solutionContent ? (
                  <div style={{ height: "80%", display: "flex", alignItems: "center", justifyContent: "center" }}>
                    <div style={{ textAlign: "center" }}>
                      <motion.div
                        animate={{ rotate: 360 }}
                        transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                        style={{ width: "30px", height: "30px", border: "3px solid var(--primary)", borderTopColor: "transparent", borderRadius: "50%", margin: "0 auto 1rem" }}
                      />
                      <p style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>AI가 실시간으로 분석을 시작합니다... (잠시만 기다려 주세요)</p>
                    </div>
                  </div>
                ) : solutionContent || selectedSolution ? (
                  <div className="markdown-content">
                    <ReactMarkdown
                      remarkPlugins={[remarkMath]}
                      rehypePlugins={[rehypeKatex]}
                    >
                      {solutionContent}
                    </ReactMarkdown>
                  </div>
                ) : (
                  <div style={{ height: "80%", display: "flex", alignItems: "center", justifyContent: "center", color: "var(--text-muted)" }}>
                    {selectedPdf ? "오른쪽 상단의 '선택한 PDF 분석 시작' 버튼을 눌러 해설을 생성하세요." : "항목을 선택하면 AI 분석 내용이 표시됩니다."}
                  </div>
                )}
              </div>
            </motion.div>
          ) : (
            /* Generator View */
            <motion.div
              key="generator"
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.98 }}
              style={{ display: "grid", gridTemplateColumns: "300px 1fr", gap: "2rem", height: "calc(100% - 6rem)" }}
            >
              <div className="glass" style={{ borderRadius: "16px", padding: "1.5rem", display: "flex", flexDirection: "column", gap: "1rem" }}>
                <h3 style={{ fontSize: "0.9rem", fontWeight: 600 }}>출제 제약 조건</h3>
                <p style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>AI가 문제를 생성할 때 참고할 추가 지침을 입력하세요.</p>
                <textarea
                  value={constraints}
                  onChange={(e) => setConstraints(e.target.value)}
                  placeholder="예: 미적분 킬러 문항 위주로 출제해줘. 삼각함수 도형 문제를 하나 포함해줘."
                  style={{ flex: 1, background: "rgba(0,0,0,0.2)", border: "1px solid var(--glass-border)", borderRadius: "8px", color: "white", padding: "1rem", outline: "none", resize: "none" }}
                />
                <button
                  onClick={handleGenerate}
                  disabled={isLoading}
                  style={{ background: "var(--primary)", border: "none", color: "white", padding: "0.8rem", borderRadius: "8px", cursor: "pointer", fontWeight: 600 }}
                >
                  {isLoading ? "생성 중..." : "설계 시작"}
                </button>
              </div>

              <div className="glass" style={{ borderRadius: "16px", padding: "2.5rem", overflowY: "auto" }}>
                <div className="markdown-content">
                  {isLoading && !generatedContent ? (
                    <div style={{ height: "100%", display: "flex", alignItems: "center", justifyContent: "center" }}>
                      <div style={{ textAlign: "center" }}>
                        <motion.div
                          animate={{ rotate: 360 }}
                          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                          style={{ width: "40px", height: "40px", border: "4px solid var(--primary)", borderTopColor: "transparent", borderRadius: "50%", margin: "0 auto 1.5rem" }}
                        />
                        <p style={{ fontSize: "0.9rem", color: "var(--text-muted)" }}>최적의 문항을 설계 중입니다... 잠시만 기다려 주세요.</p>
                      </div>
                    </div>
                  ) : generatedContent ? (
                    <ReactMarkdown
                      remarkPlugins={[remarkMath]}
                      rehypePlugins={[rehypeKatex]}
                    >
                      {generatedContent}
                    </ReactMarkdown>
                  ) : (
                    <div style={{ height: "100%", display: "flex", alignItems: "center", justifyContent: "center", color: "var(--text-muted)", textAlign: "center" }}>
                      왼쪽 입력창에 조건을 입력하고 설계 시작 버튼을 눌러주세요.
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </section>
    </main>
  );
}
