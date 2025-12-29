def get_full_url(
    name,
    base_url,
    video_overview_url,
    search_url,
    search_query_parameter,
    page_index_parameter,
    url_suffix,
    query,
    page,
) -> str:
    # Method 1
    if name in [
        "XNXX",
        "RedPorn",
        "HornyBank",
        "TeensYoung",
        "HelloPorn",
        "DirtyHomeClips",
        "Eporner",
        "PornTrex",
        "PornGo",
    ]:
        full_url = base_url + search_url + "/" + query + "/" + str(page)
    # Method 2
    elif name in ["XVideos", "RedTube", "HQPorner"]:
        full_url = (
            base_url
            + "?"
            + search_query_parameter
            + "="
            + query
            + "&"
            + page_index_parameter
            + "="
            + str(page)
        )
    # Method 3
    elif name in [
        "Porn",
        "Tnaflix",
        "PornOne",
        "4Tube",
        "PornTube",
        "Bellesa",
    ]:
        full_url = (
            base_url
            + search_url
            + "?"
            + search_query_parameter
            + "="
            + query
            + "&"
            + page_index_parameter
            + "="
            + str(page)
        )
    # Method 4
    elif name in ["XHamster", "SexyPorn", "Motherless"]:
        full_url = (
            base_url
            + search_url
            + "/"
            + query
            + "?"
            + page_index_parameter
            + "="
            + str(page)
        )
    # Method 5
    elif name in ["TabooTube", "NewPorn"]:
        full_url = base_url + search_url + "/" + query
    # Other Methods
    elif name == "PornHub":
        full_url = (
            base_url
            + video_overview_url
            + "/"
            + search_url
            + "?"
            + search_query_parameter
            + "="
            + query
            + "&"
            + page_index_parameter
            + "="
            + str(page)
        )
    elif name == "SpankBang":
        full_url = (
            base_url
            + search_query_parameter
            + "/"
            + query
            + "/"
            + str(page)
            + "/"
            + "?"
            + url_suffix
        )
    elif name == "YouPorn":
        full_url = (
            base_url
            + search_url
            + "/"
            + "?"
            + search_query_parameter
            + "="
            + query
            + "&"
            + page_index_parameter
            + "="
            + str(page)
        )
    elif name == "Fuq":
        full_url = (
            base_url
            + search_url
            + "/"
            + search_query_parameter
            + "/"
            + query
            + "?"
            + page_index_parameter
            + "="
            + str(page)
        )
    elif name == "NudeVista":
        full_url = (
            base_url
            + "?"
            + search_query_parameter
            + "="
            + query
            + "&"
            + page_index_parameter
            + "="
            + str((page - 1) * 25)
        )
    elif name == "Beeg":
        full_url = base_url + query
    elif name == "SXYPrn":
        full_url = base_url + query + ".html?" + page_index_parameter + "=" + str(page)
    elif name == "YouJizz":
        full_url = base_url + search_url + "/" + query + "-" + str(page) + ".html?"
    elif name == "3Movs":
        full_url = (
            base_url + search_url + "/" + "?" + search_query_parameter + "=" + query
        )
    return full_url


mapping = {
    "60FPS": 105,
    "Amateur": 3,
    "Anal": 35,
    "Arab": 98,
    "Asian": 1,
    "Babe": "babe",
    "Babysitter": 89,
    "BBW": 6,
    "Behind The Scenes": 141,
    "Big Ass": 4,
    "Big Dick": 7,
    "Big Tits": 8,
    "Bisexual Male": 76,
    "Blonde": 9,
    "Blowjob": 13,
    "Bondage": 10,
    "Brazilian": 102,
    "British": 96,
    "Brunette": 11,
    "Bukkake": 14,
    "Cartoon": 86,
    "Casting": 90,
    "Celebrity": 12,
    "Closed Captions": 732,
    "College": "college",
    "Compilation": 57,
    "Cosplay": 241,
    "Creampie": 15,
    "Cuckold": 242,
    "Cumshot": 16,
    "Czech": 100,
    "Described Video": "described-video",
    "Double Penetration": 72,
    "Ebony": 17,
    "Euro": 55,
    "Exclusive": 115,
    "Feet": 93,
    "Female Orgasm": 502,
    "Fetish": 18,
    "Fingering": 592,
    "Fisting": 19,
    "French": 94,
    "Funny": 32,
    "Gaming": 881,
    "Gangbang": 80,
    "Gay": "gayporn",
    "German": 95,
    "Handjob": 20,
    "Hardcore": 21,
    "HD Porn": "hd",
    "Hentai": "hentai",
    "Indian": 101,
    "Interactive": "interactive",
    "Interracial": 25,
    "Italian": 97,
    "Japanese": 111,
    "Korean": 103,
    "Latina": 26,
    "Lesbian": 27,
    "Massage": 78,
    "Masturbation": 22,
    "Mature": 28,
    "MILF": 29,
    "Muscular Men": 512,
    "Music": 121,
    "Old/Young": 181,
    "Orgy": 2,
    "Parody": 201,
    "Party": 53,
    "Pissing": 211,
    "Popular With Women": "popularwithwomen",
    "Pornstar": "pornstar",
    "POV": 41,
    "Public": 24,
    "Pussy Licking": 131,
    "Reality": 31,
    "Red Head": 42,
    "Role Play": 81,
    "Romantic": 522,
    "Rough Sex": 67,
    "Russian": 99,
    "School": 88,
    "SFW": "sfw",
    "Small Tits": 59,
    "Smoking": 91,
    "Solo Female": 492,
    "Solo Male": 92,
    "Squirt": 69,
    "Step Fantasy": 444,
    "Strap On": 542,
    "Striptease": 33,
    "Tattooed Women": 562,
    "Teen": "teen",
    "Threesome": 65,
    "Toys": 23,
    "Transgender": "transgender",
    "Verified Amateurs": 138,
    "Verified Couples": 482,
    "Verified Models": 139,
    "Vintage": 43,
    "Virtual Reality": "vr",
    "Webcam": 61,
}


def get_category_number(category):
    # Check if the category is in the mapping
    if category in mapping:
        # If it is, return the corresponding value
        return mapping[category]
    else:
        # If not, return None or handle the case as needed
        return None


def get_video_overview_url(
    name,
    base_url,
    video_overview_url,
    sort_parameter,
    sort_option,
    date_filter_parameter,
    date_filter_option,
    country_filter_parameter,
    country_filter_option,
    page_index_parameter,
    url_suffix,
    page,
    category,
    has_special_category,
):
    if name in ["PornHub"]:
        # Map integer to string
        if category is None:
            full_url = (
                base_url
                + video_overview_url
                + "?"
                + sort_parameter
                + "="
                + sort_option
                + "&"
                + date_filter_parameter
                + "="
                + date_filter_option
                + "&"
                + country_filter_parameter
                + "="
                + country_filter_option
                + "&"
                + page_index_parameter
                + "="
                + str(page)
            )
        else:
            keys_with_integers = [
                key for key, value in mapping.items() if isinstance(value, int)
            ]
            if category in keys_with_integers:
                value = mapping.get(category)
                full_url = (
                    base_url
                    + video_overview_url
                    + "?"
                    + "c"
                    + "="
                    + str(value)
                    + "&"
                    + sort_parameter
                    + "="
                    + sort_option
                    + "&"
                    + date_filter_parameter
                    + "="
                    + date_filter_option
                    + "&"
                    + country_filter_parameter
                    + "="
                    + country_filter_option
                    + "&"
                    + page_index_parameter
                    + "="
                    + str(page)
                )
            elif has_special_category:
                full_url = (
                    base_url
                    + category.lower().replace(" ", "-")
                    + "?"
                    + sort_parameter
                    + "="
                    + sort_option
                    + "&"
                    + date_filter_parameter
                    + "="
                    + date_filter_option
                    + "&"
                    + country_filter_parameter
                    + "="
                    + country_filter_option
                    + "&"
                    + page_index_parameter
                    + "="
                    + str(page)
                )
            else:
                full_url = (
                    base_url
                    + "categories"
                    + "/"
                    + category.lower()
                    + "?"
                    + sort_parameter
                    + "="
                    + sort_option
                    + "&"
                    + date_filter_parameter
                    + "="
                    + date_filter_option
                    + "&"
                    + country_filter_parameter
                    + "="
                    + country_filter_option
                    + "&"
                    + page_index_parameter
                    + "="
                    + str(page)
                )
    elif name in ["Bellesa"]:
        full_url = (
            base_url + video_overview_url + "?" + page_index_parameter + "=" + str(page)
        )
    return full_url
