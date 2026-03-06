"use client";

import { motion } from "framer-motion";
import { Folder, Files, PlusCircle, LogOut, ChevronRight, Bookmark } from "lucide-react";

interface SidebarProps {
    solutions: string[];
    pdfs: string[];
    generatedList: any[];
    selectedSolution: string | null;
    selectedPdf: string | null;
    selectedGeneratedId: number | null;
    onSelectSolution: (filename: string) => void;
    onSelectPdf: (filename: string) => void;
    onSelectGenerated: (id: number) => void;
    activeTab: "viewer" | "generator";
    setActiveTab: (tab: "viewer" | "generator") => void;
}

export default function Sidebar({
    solutions,
    pdfs,
    generatedList,
    selectedSolution,
    selectedPdf,
    selectedGeneratedId,
    onSelectSolution,
    onSelectPdf,
    onSelectGenerated,
    activeTab,
    setActiveTab
}: SidebarProps) {
    const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        const formData = new FormData();
        formData.append("file", file);

        try {
            const res = await fetch("http://localhost:8000/api/upload", {
                method: "POST",
                body: formData,
            });
            if (res.ok) {
                // Simple way to refresh: just reload or you could pass a refresh handler
                window.location.reload();
            }
        } catch (error) {
            console.error("Upload failed:", error);
        }
    };

    return (
        <aside
            style={{
                width: "280px",
                background: "var(--sidebar-bg)",
                borderRight: "1px solid var(--glass-border)",
                display: "flex",
                flexDirection: "column",
                padding: "1.5rem"
            }}
        >
            <div style={{ display: "flex", alignItems: "center", gap: "0.8rem", marginBottom: "2.5rem", paddingLeft: "0.5rem" }}>
                <div style={{ background: "linear-gradient(135deg, var(--primary), var(--secondary))", width: "32px", height: "32px", borderRadius: "8px", display: "flex", alignItems: "center", justifyContent: "center" }}>
                    <Bookmark size={18} color="white" />
                </div>
                <span style={{ fontWeight: 800, fontSize: "1.2rem", letterSpacing: "-0.5px" }}>AI_KICE</span>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem", marginBottom: "2rem" }}>
                <button
                    onClick={() => setActiveTab("viewer")}
                    style={{
                        display: "flex", alignItems: "center", gap: "0.8rem", padding: "0.8rem 1rem", borderRadius: "10px",
                        border: "none", background: activeTab === "viewer" ? "rgba(255,255,255,0.05)" : "transparent",
                        color: activeTab === "viewer" ? "var(--foreground)" : "var(--text-muted)", cursor: "pointer",
                        textAlign: "left"
                    }}
                >
                    <Folder size={18} />
                    <span style={{ fontWeight: 500 }}>문제 분석 뷰어</span>
                </button>
                <button
                    onClick={() => setActiveTab("generator")}
                    style={{
                        display: "flex", alignItems: "center", gap: "0.8rem", padding: "0.8rem 1rem", borderRadius: "10px",
                        border: "none", background: activeTab === "generator" ? "rgba(255,255,255,0.05)" : "transparent",
                        color: activeTab === "generator" ? "var(--foreground)" : "var(--text-muted)", cursor: "pointer",
                        textAlign: "left"
                    }}
                >
                    <PlusCircle size={18} />
                    <span style={{ fontWeight: 500 }}>AI 문제 생성기</span>
                </button>
            </div>

            <div style={{ flex: 1, overflowY: "auto" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem", paddingLeft: "1rem", paddingRight: "0.5rem" }}>
                    <h3 style={{ fontSize: "0.75rem", textTransform: "uppercase", letterSpacing: "1px", color: "var(--text-muted)" }}>문제지 (PDF)</h3>
                    <label style={{ cursor: "pointer", display: "flex", color: "var(--primary)" }} title="새 PDF 업로드">
                        <PlusCircle size={16} />
                        <input type="file" accept=".pdf" style={{ display: "none" }} onChange={handleUpload} />
                    </label>
                </div>

                <div style={{ display: "flex", flexDirection: "column", gap: "2px", marginBottom: "2rem" }}>
                    {pdfs.map((pdf) => (
                        <motion.div
                            key={pdf}
                            whileHover={{ x: 4 }}
                            onClick={() => {
                                onSelectPdf(pdf);
                                setActiveTab("viewer");
                            }}
                            style={{
                                padding: "0.6rem 1rem",
                                borderRadius: "8px",
                                fontSize: "0.85rem",
                                cursor: "pointer",
                                background: selectedPdf === pdf ? "rgba(168, 85, 247, 0.1)" : "transparent",
                                color: selectedPdf === pdf ? "var(--secondary)" : "var(--foreground)",
                                display: "flex",
                                alignItems: "center",
                                gap: "0.5rem"
                            }}
                        >
                            <Files size={14} />
                            <span style={{ whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                                {pdf}
                            </span>
                        </motion.div>
                    ))}
                </div>

                <h3 style={{ fontSize: "0.75rem", textTransform: "uppercase", letterSpacing: "1px", color: "var(--text-muted)", marginBottom: "1rem", paddingLeft: "1rem" }}>생성된 해설지</h3>
                <div style={{ display: "flex", flexDirection: "column", gap: "2px", marginBottom: "2rem" }}>
                    {solutions.map((sol) => (
                        <motion.div
                            key={sol}
                            whileHover={{ x: 4 }}
                            onClick={() => onSelectSolution(sol)}
                            style={{
                                padding: "0.6rem 1rem",
                                borderRadius: "8px",
                                fontSize: "0.85rem",
                                cursor: "pointer",
                                background: selectedSolution === sol ? "rgba(99, 102, 241, 0.1)" : "transparent",
                                color: selectedSolution === sol ? "var(--primary)" : "var(--foreground)",
                                display: "flex",
                                alignItems: "center",
                                justifyContent: "space-between"
                            }}
                        >
                            <span style={{ whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                                {sol.replace("_solutions.md", "")}
                            </span>
                            {selectedSolution === sol && <ChevronRight size={14} />}
                        </motion.div>
                    ))}
                    {solutions.length === 0 && (
                        <div style={{ padding: "1rem", fontSize: "0.8rem", color: "var(--text-muted)", textAlign: "center" }}>
                            저장된 해설지가 없습니다
                        </div>
                    )}
                </div>

                <h3 style={{ fontSize: "0.75rem", textTransform: "uppercase", letterSpacing: "1px", color: "var(--text-muted)", marginBottom: "1rem", paddingLeft: "1rem" }}>AI 생성 내역</h3>
                <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                    {generatedList.map((item) => (
                        <motion.div
                            key={item.id}
                            whileHover={{ x: 4 }}
                            onClick={() => onSelectGenerated(item.id)}
                            style={{
                                padding: "0.6rem 1rem",
                                borderRadius: "8px",
                                fontSize: "0.85rem",
                                cursor: "pointer",
                                background: selectedGeneratedId === item.id ? "rgba(20, 184, 166, 0.1)" : "transparent",
                                color: selectedGeneratedId === item.id ? "var(--accent)" : "var(--foreground)",
                                display: "flex",
                                flexDirection: "column",
                                gap: "2px"
                            }}
                        >
                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                                <span style={{ fontWeight: 600 }}>Problem #{item.id}</span>
                                <span style={{ fontSize: "0.7rem", opacity: 0.6 }}>{item.difficulty}</span>
                            </div>
                            <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>
                                {new Date(item.created_at).toLocaleDateString()}
                            </span>
                        </motion.div>
                    ))}
                    {generatedList.length === 0 && (
                        <div style={{ padding: "1rem", fontSize: "0.8rem", color: "var(--text-muted)", textAlign: "center" }}>
                            생성 내역이 없습니다
                        </div>
                    )}
                </div>
            </div>

            <div style={{ marginTop: "auto", paddingTop: "1.5rem", borderTop: "1px solid var(--glass-border)" }}>
                <button style={{ background: "transparent", border: "none", color: "var(--text-muted)", display: "flex", alignItems: "center", gap: "0.5rem", cursor: "pointer", fontSize: "0.9rem" }}>
                    <LogOut size={16} />
                    <span>시스템 종료</span>
                </button>
            </div>
        </aside>
    );
}
