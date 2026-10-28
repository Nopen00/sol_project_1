import type { NewsVideo } from "../types/news";
import "./VideoCard.css";

const VideoCard = ({ video }: { video: NewsVideo }) => {
  return (
    <div className="video-card">
      <img
        className="video-card__thumb"
        src={video.thumbnail_url}
        alt={`${video.title}의 썸네일`}
      ></img>
      <div className="video-card__body">
        <h3>{video.title}</h3>
        <p>채널명 : {video.channel_title}</p>
        <p>게시 시간 : {video.published_at}</p>
      </div>
      <div className="go_video_box">
        <a
          className="go_video"
          href={`https://www.youtube.com/watch?v=${video.video_id}`}
          target="_blank"
          rel="noopener noreferrer"
        >
          영상 보러가기
        </a>
      </div>
    </div>
  );
};

export default VideoCard;
