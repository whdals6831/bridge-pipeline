# Perception Pipeline

이 context는 카메라 또는 비디오 입력에서 프레임을 얻고 후속 perception 처리를 위해 ROS 메시지로 흘려보내는 pipeline을 다룬다.

## Language

**Camera session**:
로컬 카메라 입력을 열고, 프레임을 읽고, 실패 후 다시 연결될 수 있는 하나의 실행 중인 카메라 획득 흐름.
_Avoid_: camera handler, capture wrapper
