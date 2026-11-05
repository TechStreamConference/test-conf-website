// The icons are from Font Awesome Free (https://fontawesome.com), licensed under CC BY 4.0
// (https://creativecommons.org/licenses/by/4.0/).
import { faBluesky } from '@fortawesome/free-brands-svg-icons';
import { faDiscord } from '@fortawesome/free-brands-svg-icons';
import { faGithub } from '@fortawesome/free-brands-svg-icons';
import { faDownload } from '@fortawesome/free-solid-svg-icons';
import { faGlobe } from '@fortawesome/free-solid-svg-icons';
import { faInstagram } from '@fortawesome/free-brands-svg-icons';
import { faLinkedin } from '@fortawesome/free-brands-svg-icons';
import { faMastodon } from '@fortawesome/free-brands-svg-icons';
import { faTwitch } from '@fortawesome/free-brands-svg-icons';
import { faXTwitter } from '@fortawesome/free-brands-svg-icons';
import { faYoutube } from '@fortawesome/free-brands-svg-icons';

/**
 * @brief The social media networks that can be linked and shown as an icon.
 *
 * The numeric values are stored in the backend. They must NEVER be changed or removed.
 * New networks may only be added, each with a new, unused value.
 * A network that is not used anymore stays in the enum, so its value is never given out again.
 */
export enum SocialNetwork {
    Twitch = 1,
    YouTube = 2,
    Discord = 3,
    GitHub = 4,
    Mastodon = 5,
    Bluesky = 6,
    X = 7,
    Instagram = 8,
    LinkedIn = 9,
    Website = 10, // Not a social network, but the icon for every other link.
    Download = 11 // Not a social network, but the icon for a link to a file, e.g. a press kit.
}

interface SocialNetworkIcon {
    width: number;
    height: number;
    path: string;
}

interface SocialNetworkInfo {
    label: string;
    icon: SocialNetworkIcon;
}

/**
 * @brief Converts a Font Awesome icon into the data that is needed to draw it.
 * @param definition the Font Awesome icon
 * @returns the size of the icon and its svg path
 * @throws if the icon has more than one path (only duotone icons have)
 */
function toIcon(definition: typeof faTwitch): SocialNetworkIcon {
    const [width, height, , , path] = definition.icon;
    if (typeof path !== 'string') {
        throw new Error(`The icon '${definition.iconName}' has more than one path.`);
    }
    return { width, height, path };
}

/**
 * @brief The label and the icon of every social media network.
 *
 * The type makes TypeScript report a newly added network that is missing here.
 */
export const SOCIAL_NETWORKS: Record<SocialNetwork, SocialNetworkInfo> = {
    [SocialNetwork.Twitch]: { label: 'Twitch', icon: toIcon(faTwitch) },
    [SocialNetwork.YouTube]: { label: 'YouTube', icon: toIcon(faYoutube) },
    [SocialNetwork.Discord]: { label: 'Discord', icon: toIcon(faDiscord) },
    [SocialNetwork.GitHub]: { label: 'GitHub', icon: toIcon(faGithub) },
    [SocialNetwork.Mastodon]: { label: 'Mastodon', icon: toIcon(faMastodon) },
    [SocialNetwork.Bluesky]: { label: 'Bluesky', icon: toIcon(faBluesky) },
    [SocialNetwork.X]: { label: 'X', icon: toIcon(faXTwitter) },
    [SocialNetwork.Instagram]: { label: 'Instagram', icon: toIcon(faInstagram) },
    [SocialNetwork.LinkedIn]: { label: 'LinkedIn', icon: toIcon(faLinkedin) },
    [SocialNetwork.Website]: { label: 'Website', icon: toIcon(faGlobe) },
    [SocialNetwork.Download]: { label: 'Download', icon: toIcon(faDownload) }
};

/**
 * @brief All social media networks as value and label pairs, e.g. for a dropdown.
 */
export const SOCIAL_NETWORK_OPTIONS: { value: SocialNetwork; label: string }[] = Object.values(
    SocialNetwork
)
    .filter((value): value is SocialNetwork => typeof value === 'number')
    .map((value) => ({ value, label: SOCIAL_NETWORKS[value].label }));

/**
 * @brief Checks whether a number, e.g. from the backend, is a known social media network.
 * @param value the number to check
 * @returns true if the number is a value of the SocialNetwork enum
 */
export function isSocialNetwork(value: number): value is SocialNetwork {
    return value in SOCIAL_NETWORKS;
}
