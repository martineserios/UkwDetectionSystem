import argparse
import cv2
import boto3
import os
import sys
from dotenv import load_dotenv

def upload_to_s3(file_path, bucket_name, s3_path):
    s3 = boto3.client('s3')
    s3.upload_file(file_path, bucket_name, s3_path)
    print(f"Uploaded {file_path} to s3://{bucket_name}/{s3_path}")
    sys.stdout.flush()

def sample_frames(video_path, frames_per_second, bucket_name):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Cannot open video file {video_path}")
        sys.stdout.flush()
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_interval = int(fps // frames_per_second)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"Video FPS: {fps}")
    print(f"Frame interval: {frame_interval}")
    print(f"Total frames in video: {total_frames}")
    sys.stdout.flush()

    count = 0
    frame_count = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        if count % frame_interval == 0:
            frame_filename = f"frame_{frame_count:04d}.jpg"
            cv2.imwrite(frame_filename, frame)
            s3_path = os.path.join('frames', frame_filename)
            upload_to_s3(frame_filename, bucket_name, s3_path)
            os.remove(frame_filename)
            print(f"Processed and uploaded frame {frame_count}")
            sys.stdout.flush()
            frame_count += 1
        
        count += 1
        if count % 100 == 0:
            print(f"Processed {count} frames out of {total_frames}")
            sys.stdout.flush()

    print(f"Total frames processed: {frame_count}")
    sys.stdout.flush()
    cap.release()

def main(args):
    sample_frames(args.video_path, args.frames_per_second, args.bucket_name)

if __name__ == "__main__":
    load_dotenv()  # Load environment variables from .env file

    parser = argparse.ArgumentParser(description="Sample frames from a video and upload to S3.")
    parser.add_argument('video_path', type=str, help='The path to the video file')
    parser.add_argument('frames_per_second', type=int, help='Number of frames to sample per second')
    parser.add_argument('bucket_name', type=str, help='The name of the S3 bucket')
    
    args = parser.parse_args()
    main(args)

