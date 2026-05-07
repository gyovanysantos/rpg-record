import { Routes, Route, Navigate } from "react-router-dom";
import { useAppStore } from "./stores/appStore";
import RolePicker from "./components/layout/RolePicker";
import AppLayout from "./components/layout/AppLayout";
import DashboardPage from "./pages/DashboardPage";
import CharactersPage from "./pages/CharactersPage";
import CharacterSheetPage from "./pages/CharacterSheetPage";
import SpellsPage from "./pages/SpellsPage";
import TalentsPage from "./pages/TalentsPage";
import DicePage from "./pages/DicePage";
import InitiativePage from "./pages/InitiativePage";
import RecorderPage from "./pages/RecorderPage";
import TranscriptsPage from "./pages/TranscriptsPage";
import NarratorPage from "./pages/NarratorPage";
import SettingsPage from "./pages/SettingsPage";

export default function App() {
  const role = useAppStore((s) => s.role);

  if (!role) {
    return <RolePicker />;
  }

  return (
    <AppLayout>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/characters" element={<CharactersPage />} />
        <Route path="/characters/:filename" element={<CharacterSheetPage />} />
        <Route path="/spells" element={<SpellsPage />} />
        <Route path="/talents" element={<TalentsPage />} />
        <Route path="/dice" element={<DicePage />} />
        <Route path="/initiative" element={<InitiativePage />} />
        {role === "dm" && (
          <>
            <Route path="/recorder" element={<RecorderPage />} />
            <Route path="/transcripts" element={<TranscriptsPage />} />
            <Route path="/narrator" element={<NarratorPage />} />
          </>
        )}
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppLayout>
  );
}
