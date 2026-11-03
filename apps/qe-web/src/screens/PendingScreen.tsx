import { Panel, Screen } from "../ui/layout";

export function PendingScreen({ title }: { title: string }) {
  return (
    <Screen title={title} lead="This stage has not run for project billing yet.">
      <Panel>
        <p className="text-[17px] text-ink-2">Results appear here once the stage has run.</p>
      </Panel>
    </Screen>
  );
}
