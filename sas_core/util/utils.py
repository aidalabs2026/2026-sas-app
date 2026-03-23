def get_channels(center_freq_mhz: int, bandwidth_mhz: int, base_freq=3300, channel_width=10):
    """
    center_freq_mhz : 중심 주파수 (MHz)
    bandwidth_mhz   : 라이선스 대역폭 (MHz)
    base_freq       : 채널 1의 중심 주파수 기준 (기본값 3305MHz 라고 가정)
    channel_width   : 채널 폭 (MHz, 기본 10MHz)

    return: 점유 채널 번호 리스트 (마지막 겹치는 채널 제외)
    """
    half_bw = bandwidth_mhz / 2
    start_freq = center_freq_mhz - half_bw
    end_freq = center_freq_mhz + half_bw

    channels = []
    ch_num = 1
    freq = base_freq
    while freq <= 4000:  # 상한선 넉넉히 설정
        ch_start = freq - channel_width / 2
        ch_end = freq + channel_width / 2

        # 마지막 채널 제외: 채널 시작이 점유 구간 끝보다 작은 경우까지만 포함
        if ch_end > start_freq and ch_start < end_freq:
            # 단, 끝 주파수와 정확히 맞닿은 마지막 채널은 제외
            if ch_end <= end_freq:
                channels.append(ch_num)

        freq += channel_width
        ch_num += 1

    return channels