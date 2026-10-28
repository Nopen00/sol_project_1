import { useEffect, useState } from "react";
import { getNewsVideos } from "../api/news";
import VideoCard from "../components/VideoCard";
import type { NewsVideo } from "../types/news";
import "./News.css"

const News = () => {
    const [videos, setVideos] = useState<NewsVideo[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");



    useEffect(()=>{
        getNewsVideos()
        .then((data)=> setVideos(data.items))
        .catch((err:unknown)=>
            setError(err instanceof Error ? err.message : '오류')
        )
        .finally(() => setLoading(false))
    },[])

    if(loading){
        return "불러오는 중"
    }
    
    if(error){
        return error
    }

    return (
        <div className="news-page">
            <div className="news-pag-header">
                <h1 className="">Drone News</h1>

                <p className="">최신 드론 정보를 확인하세요.</p>
            </div>


            <section className="news-video">
                <div className="news-videocard">
                    {videos.map((item)=> <VideoCard video={item} key={item.video_id}></VideoCard>)}
                </div>
            </section>


        </div>
    );
};

export default News;