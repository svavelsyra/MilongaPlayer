import pickle


def convert():
    try:
        # Update cashe
        with open('cashe.dat', 'br') as fh:
            p = pickle.load(fh)

        version = p.get('version', 0)
        if not version:
            pass
    except:
        pass

    try:
        # Update playlists
        with open('playlists.dat', 'br') as fh:
            p = pickle.load(fh)
        version = p.get('version', 0)

        # Update from version 0 to version 1
        if not version:
            for pl in p['playlists']:
                if pl['type'] == 'Pattern':
                    for pattern in pl['playlist']:
                        pattern.playlist = pattern.play_list
                        delattr(pattern, 'play_list')
            p['version'] = 1

        # Save result    
        with open('playlists.dat', 'bw') as fh:
            pickle.dump(p, fh)
    except:
        pass
