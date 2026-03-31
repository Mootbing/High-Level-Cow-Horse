import { PROJECTS } from "@/lib/projects";
import { notFound } from "next/navigation";
import CaseStudyClient from "./CaseStudyClient";

export function generateStaticParams() {
  return PROJECTS.map((p) => ({ slug: p.slug }));
}

export function generateMetadata({ params }: { params: Promise<{ slug: string }> }) {
  // For static export, we need sync access — use a workaround
  return params.then(({ slug }) => {
    const project = PROJECTS.find((p) => p.slug === slug);
    if (!project) return { title: "Not Found" };
    return {
      title: `${project.name} — Case Study | Clarmi Design Studio`,
      description: project.brief,
    };
  });
}

export default async function CaseStudyPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const project = PROJECTS.find((p) => p.slug === slug);
  if (!project) notFound();

  return <CaseStudyClient project={project} />;
}
