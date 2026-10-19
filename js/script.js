const backToTop = document.querySelector('.back-to-top');
const about = document.querySelector('#about');

function updateBackToTop() {
  const threshold = (about?.offsetTop ?? window.innerHeight) - 120;
  backToTop?.classList.toggle('is-visible', window.scrollY >= threshold);
}

backToTop?.addEventListener('click', () => {
  window.scrollTo({ top: 0, behavior: 'smooth' });
});

window.addEventListener('scroll', updateBackToTop, { passive: true });
window.addEventListener('resize', updateBackToTop);
updateBackToTop();

document.querySelectorAll('.team-photo').forEach((photo) => {
  const revealPhoto = () => photo.parentElement?.classList.add('has-photo');
  const hidePhoto = () => { photo.hidden = true; };

  photo.addEventListener('load', revealPhoto);
  photo.addEventListener('error', hidePhoto);

  if (photo.complete) {
    if (photo.naturalWidth > 0) revealPhoto();
    else hidePhoto();
  }
});
