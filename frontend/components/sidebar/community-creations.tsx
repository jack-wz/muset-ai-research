import React from "react";
import { Card } from "../ui/card";
import { CaretDown, ArrowRight, FilmStrip, Article, MusicNote, Camera } from "phosphor-react";

const CREATION_TYPES = {
  "分镜头脚本": { icon: FilmStrip, color: "text-blue-500" },
  "卡通视频": { icon: FilmStrip, color: "text-purple-500" },
  "图片生成": { icon: Camera, color: "text-pink-500" },
  "新闻报道": { icon: Article, color: "text-green-500" },
  "音乐视频": { icon: MusicNote, color: "text-red-500" },
};

const SAMPLE_CREATIONS = [
  {
    id: "1",
    title: "AI 写作的未来",
    type: "新闻报道",
    author: "陈莎拉",
    coverGradient: "from-blue-400 to-indigo-500",
  },
  {
    id: "2",
    title: "赛博朋克城市景观",
    type: "图片生成",
    author: "麦克·约翰逊",
    coverGradient: "from-pink-400 to-rose-500",
  },
  {
    id: "3",
    title: "清晨爵士韵律",
    type: "音乐视频",
    author: "李亚历克斯",
    coverGradient: "from-amber-400 to-orange-500",
  },
];

export function CommunityCreations() {
  const [isExpanded, setIsExpanded] = React.useState(true);

  return (
    <div className="flex-1 overflow-y-auto border-t border-gray-100 p-4">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="mb-4 flex w-full items-center justify-between text-left text-gray-600 hover:text-primary transition-colors"
      >
        <h2 className="text-xs font-semibold uppercase tracking-wider">
          {isExpanded ? "隐藏社区创作" : "社区创作"}
        </h2>
        <CaretDown
          size={16}
          className={`transition-transform ${isExpanded ? "" : "-rotate-90"}`}
        />
      </button>

      {isExpanded && (
        <>
          <div className="space-y-4">
            {SAMPLE_CREATIONS.map((creation) => {
              const TypeIcon = CREATION_TYPES[creation.type as keyof typeof CREATION_TYPES]?.icon || Article;

              return (
                <Card
                  key={creation.id}
                  className="group cursor-pointer overflow-hidden border-0 shadow-sm hover:shadow-md transition-all"
                >
                  <div className={`aspect-video bg-gradient-to-br ${creation.coverGradient} relative`}>
                    <div className="absolute top-2 left-2 flex items-center gap-1 rounded-full bg-black/30 px-2 py-1 backdrop-blur-sm">
                      <TypeIcon size={12} className="text-white" weight="fill" />
                      <span className="text-[10px] font-medium text-white">{creation.type}</span>
                    </div>
                    <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-60" />
                    <div className="absolute bottom-2 left-2 right-2">
                      <h4 className="text-sm font-semibold text-white truncate">{creation.title}</h4>
                      <div className="flex items-center gap-1 mt-1">
                        <div className="h-4 w-4 rounded-full bg-white/20" />
                        <span className="text-[10px] text-white/80">{creation.author}</span>
                      </div>
                    </div>
                  </div>
                </Card>
              );
            })}
          </div>

          <button className="glass-button mt-6 flex w-full items-center justify-center gap-2 rounded-xl py-2 text-sm font-medium text-gray-600 hover:text-primary">
            探索社区创作
            <ArrowRight size={16} />
          </button>
        </>
      )}
    </div>
  );
}
